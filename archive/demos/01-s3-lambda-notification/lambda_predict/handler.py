"""Lambda handler triggered by S3 ObjectCreated events under in/.

Reads the CSV that triggered the event, adds a `prediction` column
(1 if score > 0.5 else 0), and writes the result under out/ with the
same file name.
"""
import csv
import io
import os
import urllib.parse

import boto3

s3 = boto3.client("s3", endpoint_url="http://floci:4566")


def add_predictions(csv_text):
    """Pure transform: adds a `prediction` column (1 if score > 0.5 else 0).

    Kept free of any AWS client so it can be unit-tested without S3/Floci.
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    fieldnames = list(reader.fieldnames) + ["prediction"]

    out_buf = io.StringIO()
    writer = csv.DictWriter(out_buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in reader:
        score = float(row["score"])
        row["prediction"] = 1 if score > 0.5 else 0
        writer.writerow(row)

    return out_buf.getvalue()


def handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj["Body"].read().decode("utf-8")

        result = add_predictions(body)

        out_key = f"out/{os.path.basename(key)}"
        s3.put_object(Bucket=bucket, Key=out_key, Body=result.encode("utf-8"))

    return {"statusCode": 200}
