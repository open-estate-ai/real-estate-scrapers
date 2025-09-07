from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_sqs as sqs,
    aws_cloudwatch as cloudwatch,
    aws_iam as iam,
    CfnParameter,
    Duration,
)
from constructs import Construct
import os
import json

class ScraperStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, scraper_name: str, scraper_path: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        function_name_param = CfnParameter(self, "FunctionName", type="String", description="Lambda function name")
        target_url_param = CfnParameter(self, "TargetUrl", type="String", description="Target URL to scrape")
        schedule_expr_param = CfnParameter(self, "ScheduleExpression", type="String", description="EventBridge schedule expression (cron or rate)")
        bucket_names_param = CfnParameter(self, "BucketNames", type="String", description='JSON array string of bucket names, e.g. ["b1","b2"] or empty string "" if none')

        dlq = sqs.Queue(self, f"{scraper_name}-dlq", queue_name=f"{scraper_name}-dlq")

        asset_path = os.path.join(scraper_path, "dist", "deployment.zip")
        if not os.path.exists(asset_path):
            raise RuntimeError(f"Deployment package not found for {scraper_name}. Run build/build_scraper.sh {scraper_name} --arch x86_64 (or arm64) and ensure scrapers/{scraper_name}/dist/deployment.zip exists")

        extra_env_param = CfnParameter(
            self, "ExtraEnv",
            type="String",
            description="JSON object string of extra environment variables",
            default="{}"
        )

        # Prepare environment variables: mandatory ones plus ExtraEnv merged
        env_dict = {
            "TARGET_URL": target_url_param.value_as_string,
            "BUCKETS": bucket_names_param.value_as_string
        }

        # Note: merging ExtraEnv into env_dict. If ExtraEnv is not a valid JSON at deploy time,
        # the Lambda environment will contain the literal value; validate before deploying.
        try:
            parsed_extra = json.loads(extra_env_param.value_as_string)
            if isinstance(parsed_extra, dict):
                for k, v in parsed_extra.items():
                    env_dict[str(k)] = str(v)
        except Exception:
            # If parsing fails at synth time due to tokens, skip merging here.
            pass

        fn = _lambda.Function(
            self, f"{scraper_name}-function",
            function_name=function_name_param.value_as_string,
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="lambda_function.handler",
            code=_lambda.Code.from_asset(asset_path),
            dead_letter_queue=dlq,
            dead_letter_queue_enabled=True,
            timeout=Duration.seconds(60),
            environment=env_dict
        )

        # Grant basic S3 permissions broadly (tweak for production)
        fn.add_to_role_policy(iam.PolicyStatement(
            actions=["s3:PutObject", "s3:PutObjectAcl", "s3:ListBucket"],
            resources=["arn:aws:s3:::*"]
        ))

        rule = events.Rule(
            self, f"{scraper_name}-schedule",
            schedule=events.Schedule.expression(schedule_expr_param.value_as_string),
            targets=[targets.LambdaFunction(handler=fn)]
        )

        errors_metric = fn.metric_errors(period=Duration.minutes(1))
        alarm = cloudwatch.Alarm(
            self, f"{scraper_name}-errors-alarm",
            metric=errors_metric,
            evaluation_periods=1,
            threshold=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description=f"Alarm when {function_name_param.value_as_string} reports any errors"
        )
