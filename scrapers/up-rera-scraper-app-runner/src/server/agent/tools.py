import json
import logging
import os
from datetime import datetime
from typing import Any, List, Dict, Optional
from pathlib import Path
from urllib.parse import urlparse
from agents import function_tool

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logging.warning("⚠️  boto3 not available - S3 uploads will not work")

logging.basicConfig(
    level=logging.INFO,
    format='[TOOL] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions for S3 Upload
# ============================================================================

def make_partitioned_key(prefix: str = "data", now: Optional[datetime] = None, ext: str = "json") -> str:
    """Generate a partitioned S3 key with year/month/day structure.

    Args:
        prefix: Prefix for the key (e.g., "data", "scrapes")
        now: Datetime to use for partitioning (defaults to UTC now)
        ext: File extension (default: "json")

    Returns:
        Partitioned key like: "prefix/year=2025/month=11/day=08/20251108T123456.json"
    """
    now = now or datetime.utcnow()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    ts = now.strftime("%Y%m%dT%H%M%S")
    filename = f"{ts}.{ext}"
    return f"{prefix}/year={year}/month={month}/day={day}/{filename}"


def _ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def upload_json_to_s3(
    bucket: str,
    data: Any,
    prefix: str = "scrapes",
    s3_client=None,
    local_output_dir_env: str = "LOCAL_OUTPUT_DIR",
    content_type: str = "application/x-ndjson"
) -> Dict[str, str]:
    """
    Save data as newline-delimited JSON (NDJSON) to:
    - local directory (when bucket == "LOCAL"),
    - file:// path,
    - or S3.

    Args:
        bucket: S3 bucket name, "LOCAL", or "file://path"
        data: Data to upload (dict or list of dicts)
        prefix: Prefix for partitioned key (e.g., "scrapes", "up-rera-projects")
        s3_client: Optional boto3 S3 client (created if not provided)
        local_output_dir_env: Environment variable name for local output directory
        content_type: MIME type for the uploaded content

    Returns:
        Dict with keys: type, target, key, url (for S3)
    """
    # Always work with a list of records
    if not isinstance(data, list):
        data = [data]

    # Convert records to NDJSON string
    ndjson_data = "\n".join(json.dumps(record, default=str)
                            for record in data) + "\n"

    # Case 1: Local output dir
    if bucket == "LOCAL":
        local_dir = os.environ.get(local_output_dir_env)
        if not local_dir:
            raise ValueError(
                f"Environment variable {local_output_dir_env} not set for LOCAL bucket")

        key = make_partitioned_key(prefix=prefix)
        path = os.path.join(local_dir, key)
        _ensure_dir(os.path.dirname(path))

        with open(path, "w", encoding="utf-8") as f:
            f.write(ndjson_data)

        logger.info(f"💾 Saved to local file: {path}")
        return {"type": "file", "target": local_dir, "key": path}

    # Case 2: file:// destination
    if bucket.startswith("file://"):
        parsed = urlparse(bucket)
        root = parsed.path or parsed.netloc
        if not root.startswith("/"):
            root = os.path.abspath(root)

        key = make_partitioned_key(prefix=prefix)
        path = os.path.join(root, key)
        _ensure_dir(os.path.dirname(path))

        with open(path, "w", encoding="utf-8") as f:
            f.write(ndjson_data)

        logger.info(f"💾 Saved to file:// path: {path}")
        return {"type": "file", "target": root, "key": path}

    # Case 3: Upload to S3
    if not BOTO3_AVAILABLE:
        raise ImportError(
            "boto3 is required for S3 uploads. Install with: pip install boto3")

    s3_client = s3_client or boto3.client("s3")
    key = make_partitioned_key(prefix=prefix)

    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=ndjson_data.encode("utf-8"),
        ContentType=content_type
    )

    s3_url = f"s3://{bucket}/{key}"
    logger.info(f"☁️  Uploaded to S3: {s3_url}")

    return {
        "type": "s3",
        "target": bucket,
        "key": key,
        "url": s3_url
    }


@function_tool
def upload_to_s3(file_path: str, bucket: str, prefix: str = "up-rera-projects") -> str:
    """Upload scraped UP RERA project data to AWS S3 with partitioned keys.

    Uploads the JSON file to S3 using a partitioned key structure:
    s3://bucket/prefix/year=YYYY/month=MM/day=DD/YYYYMMDDTHHmmss.json

    Supports three destination types:
    1. S3 bucket: bucket="my-bucket-name"
    2. Local directory: bucket="LOCAL" (requires LOCAL_OUTPUT_DIR env var)
    3. File path: bucket="file:///path/to/dir"

    Args:
        file_path: Absolute path to the JSON file to upload (from scrape_projects_list)
        bucket: S3 bucket name, "LOCAL", or "file://path"
        prefix: S3 key prefix for organizing data (default: "up-rera-projects")

    Returns:
        JSON string containing:
        - status: "success" or "error"
        - upload_type: "s3", "file", or "local"
        - bucket/target: Destination identifier
        - s3_key: Full S3 key or file path
        - s3_url: Full S3 URL (for S3 uploads)
        - file_size: Original file size in bytes
        - total_projects: Number of projects uploaded
        - message: Human-readable status message
    """
    try:
        logger.info("☁️  Starting S3 upload...")
        logger.info(f"   Source file: {file_path}")
        logger.info(f"   Destination: {bucket}")
        logger.info(f"   Prefix: {prefix}")

        # Check if source file exists
        filepath = Path(file_path)
        if not filepath.exists():
            logger.error(f"❌ Source file not found: {file_path}")
            return json.dumps({
                "status": "error",
                "message": "Source file not found",
                "error": f"The file {file_path} does not exist"
            })

        # Read the JSON file
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info("   ✅ Source file loaded successfully")

        # Extract project data for NDJSON format
        data_obj = data.get("data", {})
        projects = data_obj.get("projects", [])

        if not projects:
            logger.warning("⚠️  No projects found in file")
            return json.dumps({
                "status": "error",
                "message": "No projects found",
                "error": "The file contains no project data to upload"
            })

        logger.info(f"   Total projects to upload: {len(projects)}")

        # Upload to S3 (or local/file)
        upload_result = upload_json_to_s3(
            bucket=bucket,
            data=projects,  # Upload projects as NDJSON
            prefix=prefix
        )

        logger.info(f"   ✅ Upload complete!")
        logger.info(f"   Type: {upload_result['type']}")
        logger.info(f"   Key: {upload_result['key']}")
        if upload_result.get('url'):
            logger.info(f"   URL: {upload_result['url']}")

        # Build response
        result = {
            "status": "success",
            "upload_type": upload_result["type"],
            "bucket": bucket,
            "target": upload_result["target"],
            "s3_key": upload_result["key"],
            "file_size": filepath.stat().st_size,
            "file_size_kb": round(filepath.stat().st_size / 1024, 2),
            "total_projects": len(projects),
            "run_id": data_obj.get('run_id', 'N/A'),
            "scraped_at": data_obj.get('scraped_at', 'N/A'),
            "message": f"Successfully uploaded {len(projects)} projects to {bucket}"
        }

        # Add S3 URL if available
        if upload_result.get('url'):
            result["s3_url"] = upload_result["url"]

        logger.info(f"\n✅ Upload to S3 complete!")
        return json.dumps(result, indent=2)

    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        return json.dumps({
            "status": "error",
            "message": "Missing boto3 dependency",
            "error": str(e),
            "hint": "Install boto3 with: pip install boto3"
        })
    except Exception as e:
        logger.error(f"❌ Failed to upload to S3: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return json.dumps({
            "status": "error",
            "message": "S3 upload failed",
            "error": str(e),
            "file_path": file_path,
            "bucket": bucket
        })
