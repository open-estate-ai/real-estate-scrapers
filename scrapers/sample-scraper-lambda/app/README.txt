Scraper: sample_scraper

Purpose:
This scraper demonstrates scraping a TARGET_URL and uploading JSON payloads to zero, one, or multiple targets.
It supports:
- S3 uploads (bucket names),
- Local filesystem writes via 'LOCAL' sentinel or file:// URI.

Files:
- lambda_function.py  : Lambda handler that scrapes TARGET_URL and uploads results.
- utils.py            : Helper with make_partitioned_key and upload_json_to_s3 (supports file:// and LOCAL).
- requirements.txt    : Python dependencies for the scraper.
- run_local.py        : Helper to run the handler locally for testing.

---
Setup virtual environment (per scraper):

1. Go to the scraper folder:
   cd scrapers/sample-scraper-lambda

2. Create a virtual environment for this scraper:
   python3 -m venv .venv

3. Activate the environment:
   - macOS/Linux:   source .venv/bin/activate
   - Windows PowerShell: .venv\Scripts\Activate.ps1

4. Install dependencies:
   pip install -r requirements.txt

5. Run locally:

   a) Local output using LOCAL sentinel:
      export LOCAL_OUTPUT_DIR=./local_out
      export BUCKETS='["LOCAL"]'
      export TARGET_URL='https://example.com'
      python3 run_local.py

   b) Local output using file:// path:
      export BUCKETS='["file://./local_out_path"]'
      export TARGET_URL='https://example.com'
      python3 run_local.py

   c) No upload:
      export BUCKETS=''
      export TARGET_URL='https://example.com'
      python3 run_local.py

6. Deactivate when done:
   deactivate

---
Using .env for local runs

Place a `.env` file in this scraper folder (do NOT commit it). You can start from `.env.example` and update values.

The local runner `run_local.py` will automatically load `.env` if `python-dotenv` is installed in the scraper venv.

To install python-dotenv in the scraper venv:

```
source .venv/bin/activate
pip install python-dotenv
```

Build for deployment:

Use build/build_scraper.sh to vendor dependencies and create zip artifacts.

Example:
  ./build/build_scraper.sh sample_scraper --arch x86_64 --set-default

Deploying with CDK:
  cdk deploy --app "python3 app.py" --context scraper=sample_scraper ScraperStack-sample_scraper \
    --parameters FunctionName=sample_scraper-fn \
    --parameters TargetUrl=https://example.com \
    --parameters ScheduleExpression='rate(1 hour)' \
    --parameters BucketNames='["bucket-one","bucket-two"]' \
    --parameters ExtraEnv='{"API_KEY":"myapikey123","MAX_PAGES":"10"}'
