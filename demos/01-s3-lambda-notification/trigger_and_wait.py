"""Uploads in/scores.csv and polls for out/scores.csv, printing the
elapsed time until the Lambda's output shows up.
"""
import os
import time

import boto3

ENDPOINT = os.environ.get("FLOCI_ENDPOINT", "http://floci:4566")
BUCKET = "demo"
TIMEOUT_SECONDS = 180

s3 = boto3.client("s3", endpoint_url=ENDPOINT)


def main():
    content = b"score\n0.9\n0.2\n0.7\n"
    start = time.time()
    s3.put_object(Bucket=BUCKET, Key="in/scores.csv", Body=content)
    print("Uploaded in/scores.csv, waiting for out/scores.csv "
          f"(up to {TIMEOUT_SECONDS}s; the first run pulls the Lambda runtime image)...")

    deadline = start + TIMEOUT_SECONDS
    while time.time() < deadline:
        try:
            obj = s3.get_object(Bucket=BUCKET, Key="out/scores.csv")
            elapsed = time.time() - start
            print(f"out/scores.csv found after {elapsed:.2f}s")
            print("--- content ---")
            print(obj["Body"].read().decode("utf-8"))
            return
        except s3.exceptions.NoSuchKey:
            time.sleep(2)

    raise SystemExit(f"Timeout: out/scores.csv not found after {TIMEOUT_SECONDS}s")


if __name__ == "__main__":
    main()
