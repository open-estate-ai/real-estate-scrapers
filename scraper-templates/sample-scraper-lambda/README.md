# sample-scraper-lambda


- Deploys an AWS Lambda function on a schedule (EventBridge rule).  
- Runs your scraping logic and writes newline-delimited JSON to S3 with basic partitioning.  
- Sets up a Dead Letter Queue (DLQ) and a CloudWatch alarm for errors.  
- Built and deployed with AWS CDK.  
- Uses Python 3.11 runtime.  


## Pre-requisite
-  An AWS account (with admin permission locally). 
- Create IAM User and generate API Keys.
- AWS credentials configured locally (e.g. run: `aws configure` and verify with `aws sts get-caller-identity`).  
- Node.js + npm installed (needed for AWS CDK).  
- AWS CDK installed: `npm install -g aws-cdk` (or use npx).  
- Python 3.11 available.  
- (First time per account/region) Bootstrap the environment:
   ```sh
   cdk bootstrap aws://<ACCOUNT_ID>/ap-south-1
   ```

# Setup Steps

1. Copy this template folder into the scrapers directory.
2. Rename the folder to your scraper name.
3. Update cdk.json (if it references the old folder name).
4. Create the CDK virtual environment:
   ```sh
   make cdk-env
   ```
5. Build (synth) the scraper package:
   ```sh
   make cdk-synth ENV=dev
   ```
6. Deploy it:
   ```sh
   make cdk-deploy ENV=dev ARCH=x86_64
   ```
7. When you no longer need it, destroy it:
   ```sh
   make cdk-destroy
   ```

Notes:
- Change ENV or ARCH if needed.
- Run make cdk-env only once per fresh clone (reuse afterwards).


## Local Run

1. Go into the app folder:
   ```sh
   cd app
   ```

2. Copy env file and edit values:
   ```sh
   cp .env.example .env
   ```
   (open .env and set TARGET_URL, BUCKETS, etc.)

3. Create Python 3.11 virtual env:
   ```sh
   python3 -m venv .venv
   ```

4. Activate it:
   ```sh
   # macOS / Linux
   source .venv/bin/activate
   ```


5. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

6. Run locally:
   ```sh
   python run_local.py
   ```

7. When finished:
   ```sh
   deactivate
   ```

Notes:
- Remove the .venv folder if you need a clean reinstall.
- Logs print to your console.
- Output may write to local_out if configured.