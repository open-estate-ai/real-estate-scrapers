# Scraper Templates

This folder lists scraper templates you can use and adapt.

## Templates

1. **sample-scraper-lambda**  
   - Deploys an AWS Lambda function on a schedule (EventBridge rule).  
   - Runs your scraping logic and writes newline-delimited JSON to S3 with basic partitioning.  
   - Sets up a Dead Letter Queue (DLQ) and a CloudWatch alarm for errors.  
   - Built and deployed with AWS CDK.  
   - Uses Python 3.11 runtime.  

More templates will be added over time. Open an issue if you need