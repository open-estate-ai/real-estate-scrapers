# real-estate-scrapers
Data scrapers to collect real estate information from multiple sources. Standardized outputs feed into the data lake.



This repository template contains independent web scrapers deployable as separate AWS Lambda functions via AWS CDK.

Highlights:
- Each scraper is independent: own Lambda, DLQ, CloudWatch alarm, EventBridge schedule.
- Each scraper can upload results to zero, one, or multiple S3 targets, or to local filesystem for testing.
- Build scripts vendor dependencies using 'uv' (no Docker). Supports x86_64 and arm64 builds (build on matching arch for native wheels).
- Deploy a single scraper at a time by passing CDK context: --context scraper=<name>

---
Per-scraper virtual environments:

Each scraper has its own dependencies. To avoid conflicts, setup a virtual environment inside each scraper folder.

Example (sample_scraper):

1. cd scrapers/sample_scraper
2. python3 -m venv .venv
3. source .venv/bin/activate   # macOS/Linux
   .venv\Scripts\Activate.ps1 # Windows
4. pip install -r requirements.txt
5. Run tests with run_local.py (see scraper README.txt for examples)
6. deactivate when done

Repeat separately for each scraper.

---
Quick start (build & deploy):

1. From repo root: python3 -m pip install -r requirements-cdk.txt
2. cdk bootstrap aws://<ACCOUNT_ID>/ap-south-1
3. ./build/build_scraper.sh sample_scraper --arch x86_64 --set-default
4. cdk deploy --app "python3 app.py" --context scraper=sample_scraper ScraperStack-sample-scraper \
    --parameters FunctionName=sample-scraper-fn \
    --parameters TargetUrl=https://example.com \
    --parameters ScheduleExpression='rate(1 hour)' \
    --parameters BucketNames='["bucket-one"]' \
    --parameters ExtraEnv='{"API_KEY":"value"}'
