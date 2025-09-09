from aws_cdk import (
    Stack, Duration, CfnParameter, Tags,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_sqs as sqs,
    aws_cloudwatch as cloudwatch,
    aws_iam as iam,
)
from constructs import Construct
import os, json

class ScraperStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, scraper_name: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Add global tags for all resources in this stack
        Tags.of(self).add("Project", "open-estate-ai/real-estate-scrapers")
        Tags.of(self).add("Scraper", scraper_name)
        Tags.of(self).add("CreatedBy", "CDK")



        target_url = CfnParameter(self, "TargetUrl", type="String", description="Target URL")
        schedule_expr = CfnParameter(self, "ScheduleExpression", type="String", description="EventBridge schedule (cron or rate)")
        bucket_names = CfnParameter(self, "BucketNames", type="String", description='JSON array string of bucket names or empty string')

        dlq = sqs.Queue(self, f"{scraper_name}-dlq", queue_name=f"{scraper_name}-dlq")

        asset = os.path.join(os.path.dirname(__file__), "dist", "deployment.zip")
        if not os.path.exists(asset):
            raise RuntimeError(f"Deployment package not found: {asset}")

        env = {
            "TARGET_URL": target_url.value_as_string,
            "BUCKETS": bucket_names.value_as_string
        }
        # try:
        #     parsed = json.loads(extra_env.value_as_string)
        #     if isinstance(parsed, dict):
        #         for k,v in parsed.items():
        #             env[str(k)] = str(v)
        # except Exception:
        #     pass

        fn = _lambda.Function(self, f"{scraper_name}-fn",
                              function_name=f"{scraper_name}-fn",
                              runtime=_lambda.Runtime.PYTHON_3_11,
                              handler="lambda_function.handler",
                              code=_lambda.Code.from_asset(asset),
                              dead_letter_queue=dlq,
                              timeout=Duration.seconds(60),
                              environment=env)

        fn.add_to_role_policy(iam.PolicyStatement(actions=["s3:PutObject","s3:PutObjectAcl","s3:ListBucket"], resources=["arn:aws:s3:::*"]))

        events.Rule(self, f"{scraper_name}-rule",
                    schedule=events.Schedule.expression(schedule_expr.value_as_string),
                    targets=[targets.LambdaFunction(fn)])

        cloudwatch.Alarm(self, f"{scraper_name}-errors-alarm",
                         metric=fn.metric_errors(period=Duration.minutes(1)),
                         evaluation_periods=1, threshold=1,
                         treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING)
