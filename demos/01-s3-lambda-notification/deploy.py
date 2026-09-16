"""Deploys the IAM role, Lambda function, S3 bucket, permission and
notification configuration for demo 1. Idempotent: safe to re-run.
"""
import json
import os
import time
import zipfile

import boto3

ENDPOINT = os.environ.get("FLOCI_ENDPOINT", "http://floci:4566")
HERE = os.path.dirname(os.path.abspath(__file__))

ROLE_NAME = "lambda-exec-role"
FUNC_NAME = "predict"
BUCKET = "demo"

iam = boto3.client("iam", endpoint_url=ENDPOINT)
lam = boto3.client("lambda", endpoint_url=ENDPOINT)
s3 = boto3.client("s3", endpoint_url=ENDPOINT)


def build_zip():
    zip_path = os.path.join(HERE, "predict.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(os.path.join(HERE, "lambda_predict", "handler.py"), "handler.py")
    return zip_path


def ensure_role():
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
        role = iam.create_role(
            RoleName=ROLE_NAME, AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        role_arn = role["Role"]["Arn"]
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = iam.get_role(RoleName=ROLE_NAME)["Role"]["Arn"]

    # Scoped to exactly what the handler needs: read from in/, write to out/,
    # plus basic CloudWatch Logs permissions (the AWS Lambda execution-role
    # baseline). No AdministratorAccess for a function that only touches S3.
    execution_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{BUCKET}/in/*"],
            },
            {
                "Effect": "Allow",
                "Action": ["s3:PutObject"],
                "Resource": [f"arn:aws:s3:::{BUCKET}/out/*"],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                "Resource": "arn:aws:logs:*:*:*",
            },
        ],
    }
    iam.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName="predict-execution-policy",
        PolicyDocument=json.dumps(execution_policy),
    )
    return role_arn


def ensure_function(role_arn, zip_bytes):
    try:
        fn = lam.create_function(
            FunctionName=FUNC_NAME,
            Runtime="python3.12",
            Role=role_arn,
            Handler="handler.handler",
            Code={"ZipFile": zip_bytes},
            Timeout=60,
            MemorySize=256,
        )
        func_arn = fn["FunctionArn"]
    except lam.exceptions.ResourceConflictException:
        lam.update_function_code(FunctionName=FUNC_NAME, ZipFile=zip_bytes)
        func_arn = lam.get_function(FunctionName=FUNC_NAME)["Configuration"]["FunctionArn"]

    for _ in range(30):
        conf = lam.get_function_configuration(FunctionName=FUNC_NAME)
        if conf.get("State") == "Active":
            break
        time.sleep(2)
    else:
        raise RuntimeError("Lambda function did not become Active in time")

    return func_arn


def ensure_bucket():
    try:
        s3.create_bucket(Bucket=BUCKET)
    except s3.exceptions.BucketAlreadyOwnedByYou:
        pass


def ensure_permission():
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
    print("Building Lambda zip...")
    zip_path = build_zip()
    with open(zip_path, "rb") as f:
        zip_bytes = f.read()

    print("Ensuring IAM role...")
    role_arn = ensure_role()

    print("Ensuring Lambda function...")
    func_arn = ensure_function(role_arn, zip_bytes)

    print("Ensuring S3 bucket...")
    ensure_bucket()

    print("Ensuring Lambda invoke permission...")
    ensure_permission()

    print("Ensuring S3 notification configuration...")
    ensure_notification(func_arn)

    print("Deploy complete.")


if __name__ == "__main__":
    main()
