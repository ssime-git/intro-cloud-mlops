"""Lambda handler triggered by S3 ObjectCreated events under in/.

Same scoring code as on the laptop and on EC2: `add_predictions()` comes from
scoring/score.py, packaged next to this file by deploy.py. The handler only
adds the plumbing: read the file that triggered the event, write the result
under out/ with the same file name.
"""
import os
import urllib.parse

import boto3
from score import add_predictions

# On AWS, boto3 finds S3 on its own. On Floci, the Lambda container receives
# AWS_ENDPOINT_URL pointing back at the emulator, and boto3 reads it too.
s3 = boto3.client("s3")


def handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        print(f"received s3://{bucket}/{key}")

        body = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
        result = add_predictions(body)

        out_key = f"out/{os.path.basename(key)}"
        s3.put_object(Bucket=bucket, Key=out_key, Body=result.encode("utf-8"))
        rows = result.count("\n") - 1
        positives = result.count(",1\n")
        print(f"wrote s3://{bucket}/{out_key}: {rows} rows, {positives} predicted 1")

    return {"statusCode": 200}
