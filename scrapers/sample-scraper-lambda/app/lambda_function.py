import os
import json
import logging
import requests
from datetime import datetime
from utils import upload_json_to_s3

logger = logging.getLogger()
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def parse_buckets(env_val):
    if not env_val:
        return []
    env_val = env_val.strip()
    try:
        parsed = json.loads(env_val)
        if isinstance(parsed, list):
            return [str(x) for x in parsed if x]
    except Exception:
        pass
    return [p.strip() for p in env_val.split(",") if p.strip()]

def handler(event, context):
    target = os.environ.get("TARGET_URL")
    buckets_env = os.environ.get("BUCKETS", "")
    buckets = parse_buckets(buckets_env)
    logger.info("TARGET_URL=%s BUCKETS=%s", target, buckets)

    if not target:
        logger.error("Missing TARGET_URL in environment")
        raise Exception("Missing required env var TARGET_URL")

    resp = requests.get(target, timeout=30)
    resp.raise_for_status()

    payload = {
        "scraped_at": datetime.utcnow().isoformat(),
        "status_code": resp.status_code,
        "url": target,
        "headers": dict(resp.headers),
        "text_snippet": resp.text[:4096]
    }

    uploaded = []
    if buckets:
        for b in buckets:
            try:
                result = upload_json_to_s3(bucket=b, data=payload, prefix=f"scrapers/{context.function_name}")
                logger.info("Uploaded result: %s", result)
                uploaded.append(result)
            except Exception as e:
                logger.exception("Failed uploading to %s: %s", b, str(e))
                raise
    else:
        logger.info("No buckets configured; skipping S3 upload.")

    return {
        "statusCode": 200,
        "body": json.dumps({"uploaded": uploaded})
    }
