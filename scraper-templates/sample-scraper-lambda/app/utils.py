import json
import datetime
import os
import boto3
from urllib.parse import urlparse

def make_partitioned_key(prefix="data", now=None, ext="json"):
    now = now or datetime.datetime.utcnow()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    ts = now.strftime("%Y%m%dT%H%M%S")
    filename = f"{ts}.{ext}"
    return f"{prefix}/year={year}/month={month}/day={day}/{filename}"

def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def upload_json_to_s3(bucket, data, prefix="scrapes", s3_client=None, local_output_dir_env="LOCAL_OUTPUT_DIR"):
    """
    Save data as newline-delimited JSON (NDJSON) to:
    - local directory (when bucket == "LOCAL"),
    - file:// path,
    - or S3.
    """

    # Always work with a list of records
    if not isinstance(data, list):
        data = [data]

    # Convert records to NDJSON string
    ndjson_data = "\n".join(json.dumps(record, default=str) for record in data) + "\n"

    # Case 1: Local output dir
    if bucket == "LOCAL":
        local_dir = os.environ.get(local_output_dir_env)
        key = make_partitioned_key(prefix=prefix)
        path = os.path.join(local_dir, key)
        _ensure_dir(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            f.write(ndjson_data)
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
        return {"type": "file", "target": root, "key": path}

    # Case 3: Upload to S3
    s3_client = s3_client or boto3.client("s3")
    key = make_partitioned_key(prefix=prefix)
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=ndjson_data.encode("utf-8"),
        ContentType="application/x-ndjson"
    )
    return {"type": "s3", "target": bucket, "key": key}
