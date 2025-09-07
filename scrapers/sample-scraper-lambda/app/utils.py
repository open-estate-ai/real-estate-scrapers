import json
import datetime
import uuid
import os
import boto3
from urllib.parse import urlparse

def make_partitioned_key(prefix="data", now=None, ext="json"):
    now = now or datetime.datetime.utcnow()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    filename = f"{uuid.uuid4().hex}.{ext}"
    return f"{prefix}/year={year}/month={month}/day={day}/{filename}"

def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def upload_json_to_s3(bucket, data, prefix="scrapes", s3_client=None, local_output_dir_env="LOCAL_OUTPUT_DIR"):
    local_dir = os.environ.get(local_output_dir_env)
    if local_dir and bucket == "LOCAL":
        key = make_partitioned_key(prefix=prefix)
        rel_path = key
        out_path = os.path.join(local_dir, rel_path)
        _ensure_dir(os.path.dirname(out_path))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, default=str)
        return {"type": "file", "target": local_dir, "key": out_path}

    if isinstance(bucket, str) and bucket.startswith("file://"):
        parsed = urlparse(bucket)
        dest_root = parsed.path or parsed.netloc
        if not dest_root.startswith("/"):
            dest_root = os.path.abspath(dest_root)
        key = make_partitioned_key(prefix=prefix)
        out_path = os.path.join(dest_root, key)
        _ensure_dir(os.path.dirname(out_path))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, default=str)
        return {"type": "file", "target": dest_root, "key": out_path}

    s3_client = s3_client or boto3.client("s3")
    key = make_partitioned_key(prefix=prefix)
    body = json.dumps(data, default=str)
    s3_client.put_object(Bucket=bucket, Key=key, Body=body, ContentType="application/json")
    return {"type": "s3", "target": bucket, "key": key}
