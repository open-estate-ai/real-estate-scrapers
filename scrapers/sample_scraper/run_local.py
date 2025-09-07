import os
import json
import importlib
from types import SimpleNamespace

# load .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
except Exception:
    pass

TARGET_URL = os.environ.get("TARGET_URL", "https://example.com")
BUCKETS = os.environ.get("BUCKETS", '["LOCAL"]')
LOCAL_OUTPUT_DIR = os.environ.get("LOCAL_OUTPUT_DIR", "./local_data")

if "LOCAL" in BUCKETS and not os.environ.get("LOCAL_OUTPUT_DIR"):
    os.environ["LOCAL_OUTPUT_DIR"] = LOCAL_OUTPUT_DIR

import lambda_function as lf

def make_context(name="local-test-fn"):
    return SimpleNamespace(function_name=name, memory_limit_in_mb=128, invoked_function_arn="arn:aws:lambda:local", aws_request_id="local-req-1")

def run():
    event = {"source": "local.run", "time": None}
    ctx = make_context()
    result = lf.handler(event, ctx)
    print("Handler result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run()
