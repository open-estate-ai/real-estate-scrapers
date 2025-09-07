# real-estate-scrapers
Data scrapers to collect real estate information from multiple sources. Standardized outputs feed into the data lake.



This repository template contains independent web scrapers deployable as separate AWS Lambda functions via AWS CDK.

Highlights:
- Each scraper is independent: own Lambda, DLQ, CloudWatch alarm, EventBridge schedule.
- Each scraper can upload results to zero, one, or multiple S3 targets, or to local filesystem for testing.
- Build scripts vendor dependencies using 'uv' (no Docker). Supports x86_64 and arm64 builds (build on matching arch for native wheels).
- Deploy a single scraper at a time

---
Per-scraper virtual environments:

Each scraper has its own dependencies. To avoid conflicts, setup a virtual environment inside each scraper folder.

Example (sample-scraper-lambda):

1. cd scrapers/sample-scraper-lambda/app
2. python3 -m venv .venv
3. source .venv/bin/activate   # macOS/Linux
   .venv\Scripts\Activate.ps1 # Windows
4. pip install -r requirements.txt
5. Run tests with `python run_local.py`
6. deactivate when done

Repeat separately for each scraper.

---
Quick start (build & deploy) using AWS CDK:

1. To create and activate a dedicated Python virtual environment for CDK development and deployment, use:

   ```sh
    make cdk-env
   ```
2. cdk bootstrap aws://<ACCOUNT_ID>/ap-south-1
3. Build the scraper artifact:

   ```sh
   make cdk-synth ENV=dev
   ```

4. Deploy the scraper stack:

   ```sh
   make cdk-deploy ENV=dev ARCH=x86_64
   ```
5. Destroy the scraper stack:

   ```sh
   make cdk-destroy
   ```