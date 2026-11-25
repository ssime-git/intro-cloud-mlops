"""Wires S3 -> Lambda for the scoring function. Idempotent: safe to re-run.

Four things, each one a concept already seen with the CLI:

1. ensure_role()          a cap for Lambda (trust = lambda.amazonaws.com)
2. ensure_function()      hire the function; AWS answers with its ARN
3. ensure_permission()    allow S3 to call it (a policy on the function side)
4. ensure_notification()  give S3 the function's ARN

No endpoint in this file: boto3 reads AWS_ENDPOINT_URL (Floci) from the
environment, exactly as the `aws` CLI does. Against real AWS, the same code
runs unchanged.
"""
import io
import json
import time
import zipfile
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parent.parent

BUCKET = "customers-data"
FUNC_NAME = "score"
ROLE_NAME = "scoring-lambda-role"

iam = boto3.client("iam")
lam = boto3.client("lambda")
s3 = boto3.client("s3")


def build_zip():
    """The Lambda package: the handler plus the same score.py as on EC2."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(ROOT / "pipeline" / "handler.py", "handler.py")
        zf.write(ROOT / "scoring" / "score.py", "score.py")
    return buf.getvalue()


def ensure_role():
    # Who may put the cap on: the Lambda service. Same JSON as trust-ec2.json,
    # only the service name changes.
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    try:
        role_arn = iam.create_role(
            RoleName=ROLE_NAME, AssumeRolePolicyDocument=json.dumps(trust_policy)
        )["Role"]["Arn"]
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = iam.get_role(RoleName=ROLE_NAME)["Role"]["Arn"]

    # What the cap allows: scoring-s3.json, plus the right to write its logs.
    execution_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{BUCKET}/in/*",
            },
            {
                "Effect": "Allow",
                "Action": "s3:PutObject",
                "Resource": f"arn:aws:s3:::{BUCKET}/out/*",
            },
            {
                "Effect": "Allow",
                "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                "Resource": "arn:aws:logs:*:*:*",
            },
        ],
    }
    iam.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName="scoring-lambda",
        PolicyDocument=json.dumps(execution_policy),
    )
    return role_arn


def ensure_function(role_arn, zip_bytes):
    try:
        func_arn = lam.create_function(
            FunctionName=FUNC_NAME,
            Runtime="python3.12",
            Role=role_arn,
            Handler="handler.handler",
            Code={"ZipFile": zip_bytes},
            Timeout=60,
            MemorySize=256,
        )["FunctionArn"]
    except lam.exceptions.ResourceConflictException:
        lam.update_function_code(FunctionName=FUNC_NAME, ZipFile=zip_bytes)
        func_arn = lam.get_function(FunctionName=FUNC_NAME)["Configuration"]["FunctionArn"]

    for _ in range(30):
        conf = lam.get_function_configuration(FunctionName=FUNC_NAME)
        updating = conf.get("LastUpdateStatus") == "InProgress"
        if conf.get("State") == "Active" and not updating:
            return func_arn
        time.sleep(2)
    raise RuntimeError("Lambda function did not become Active in time")


def ensure_bucket():
    try:
        s3.create_bucket(Bucket=BUCKET)
    except s3.exceptions.BucketAlreadyOwnedByYou:
        pass


def ensure_permission():
    # A resource-based policy on the function: "S3, for this bucket only,
    # may invoke me".
    try:
        lam.add_permission(
            FunctionName=FUNC_NAME,
            StatementId="s3invoke",
            Action="lambda:InvokeFunction",
            Principal="s3.amazonaws.com",
            SourceArn=f"arn:aws:s3:::{BUCKET}",
        )
    except lam.exceptions.ResourceConflictException:
        pass


def ensure_notification(func_arn):
    # S3 gets the function's badge number (its ARN). Only in/ triggers it:
    # the function writes to out/, so it cannot trigger itself in a loop.
    s3.put_bucket_notification_configuration(
        Bucket=BUCKET,
        NotificationConfiguration={
            "LambdaFunctionConfigurations": [
                {
                    "LambdaFunctionArn": func_arn,
                    "Events": ["s3:ObjectCreated:*"],
                    "Filter": {"Key": {"FilterRules": [{"Name": "prefix", "Value": "in/"}]}},
                }
            ]
        },
    )


def main():
    role_arn = ensure_role()
    print(f"1. role          {role_arn}")

    func_arn = ensure_function(role_arn, build_zip())
    print(f"2. function      {func_arn}")

    ensure_bucket()
    ensure_permission()
    print(f"3. permission    s3.amazonaws.com may invoke {FUNC_NAME} for arn:aws:s3:::{BUCKET}")

    ensure_notification(func_arn)
    print(f"4. notification  s3://{BUCKET}/in/* -> {FUNC_NAME}")


if __name__ == "__main__":
    main()
