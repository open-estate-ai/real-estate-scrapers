import json
import logging
from datetime import datetime
from typing import Any, List
from pathlib import Path
from agents import function_tool

logging.basicConfig(
    level=logging.INFO,
    format='[TOOL] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# def save_scraped_data_to_file(response: Dict[str, Any]) -> Optional[str]:
#     """Save scraped data to a JSON file in /tmp directory.

#     Args:
#         response: The response from scrape_projects_list MCP tool

#     Returns:
#         Path to the saved file if successful, None otherwise
#     """
#     try:
#         # Check if scraping was successful
#         if not response.get("success", False):
#             logger.warning(
#                 "⚠️  Scraping was not successful, skipping file save")
#             logger.warning(f"Error: {response.get('error', 'Unknown error')}")
#             return None

#         # Extract data
#         data = response.get("data", {})
#         run_id = data.get("run_id", "unknown")
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

#         # Create filename with timestamp and run_id
#         filename = f"up_rera_projects_{timestamp}_{run_id}.json"
#         filepath = Path("/tmp") / filename

#         # Save to file with pretty formatting (multi-line JSON)
#         with open(filepath, 'w', encoding='utf-8') as f:
#             json.dump(response, f, indent=2, ensure_ascii=False)

#         logger.info(f"✅ Saved scraped data to: {filepath}")
#         logger.info(f"   Total projects: {data.get('total_projects', 0)}")
#         logger.info(f"   Duration: {data.get('duration_seconds', 0):.1f}s")

#         # Read and display file contents for verification
#         logger.info(f"\n📄 File contents preview (first 50 lines):")
#         with open(filepath, 'r', encoding='utf-8') as f:
#             lines = f.readlines()
#             preview_lines = lines[:50]
#             for line in preview_lines:
#                 logger.info(line.rstrip())

#             if len(lines) > 50:
#                 logger.info(f"... ({len(lines) - 50} more lines)")

#         return str(filepath)

#     except Exception as e:
#         logger.error(f"❌ Failed to save scraped data: {e}")
#         import traceback
#         logger.error(traceback.format_exc())
#         return None


@function_tool
def ingest_scraped_data(file_path: str) -> str:
    """Verify and report on the scraped UP RERA project data file.

    The scrape_projects_list MCP tool automatically saves data to /tmp.
    This tool verifies the file exists, reads it, and provides a summary.

    Args:
        file_path: The absolute path to the saved JSON file (from scrape_projects_list response's saved_file field).
                  Example: "/tmp/up_rera_projects_20251108_120000_abc123.json"

    Returns:
        JSON string containing:
        - status: "success" or "error"
        - file_path: The verified file path
        - file_size: Size in bytes
        - total_projects: Number of projects in the file
        - sample_projects: First 5 project names
        - message: Human-readable status message
        - error: Error details (on failure)
    """
    try:
        logger.info("📥 Verifying scraped data file...")
        logger.info(f"   File path: {file_path}")

        # Check if file exists
        filepath = Path(file_path)
        if not filepath.exists():
            logger.error(f"❌ File not found: {file_path}")
            return json.dumps({
                "status": "error",
                "message": "File not found",
                "error": f"The file {file_path} does not exist"
            })

        # Get file size
        file_size = filepath.stat().st_size
        logger.info(
            f"   File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")

        # Read and parse the file
        with open(filepath, 'r', encoding='utf-8') as f:
            response = json.load(f)

        logger.info("   ✅ File successfully read and parsed")

        # Extract data
        data_obj = response.get("data", {})
        projects = data_obj.get("projects", [])

        logger.info(f"   Total projects in file: {len(projects)}")
        logger.info(f"   Duration: {data_obj.get('duration_seconds', 0):.1f}s")
        logger.info(f"   Run ID: {data_obj.get('run_id', 'N/A')}")

        # Display file contents preview (first 30 lines)
        logger.info(f"\n📄 File contents preview (first 30 lines):")
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            preview_lines = lines[:30]
            for line in preview_lines:
                logger.info(line.rstrip())

            if len(lines) > 30:
                logger.info(f"... ({len(lines) - 30} more lines)")

        # Log sample projects
        logger.info(f"\n📋 Sample projects from file:")
        sample_projects = []
        for idx, project in enumerate(projects[:5], 1):  # Show first 5
            project_name = project.get('project_name', 'N/A')
            rera_number = project.get('rera_number', 'N/A')
            logger.info(f"   {idx}. {project_name} - {rera_number}")
            sample_projects.append({
                "project_name": project_name,
                "rera_number": rera_number
            })

        if len(projects) > 5:
            logger.info(f"   ... and {len(projects) - 5} more projects")

        result = {
            "status": "success",
            "file_path": str(filepath),
            "file_size": file_size,
            "file_size_kb": round(file_size / 1024, 2),
            "total_projects": len(projects),
            "sample_projects": sample_projects,
            "run_id": data_obj.get('run_id', 'N/A'),
            "duration_seconds": data_obj.get('duration_seconds', 0),
            "scraped_at": data_obj.get('scraped_at', 'N/A'),
            "message": f"Successfully verified file with {len(projects)} projects ({file_size / 1024:.2f} KB)"
        }

        logger.info(f"\n✅ Verification complete!")
        return json.dumps(result, indent=2)

    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in file: {e}")
        return json.dumps({
            "status": "error",
            "message": "Invalid JSON format in file",
            "error": str(e),
            "file_path": file_path
        })
    except Exception as e:
        logger.error(f"❌ Failed to verify file: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return json.dumps({
            "status": "error",
            "message": "File verification failed",
            "error": str(e),
            "file_path": file_path
        })
