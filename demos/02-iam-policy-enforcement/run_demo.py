"""IAM policy enforcement demo.

Requires Floci started with FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true
(see the `demo2` Makefile target / docker-compose.yml).

1. Creates IAM user `junior` and an access key for them (admin creds).
2. Calls s3.list_buckets() as `junior` -> expects AccessDenied (403).
3. Attaches an inline policy allowing s3:ListAllMyBuckets on *.
4. Calls s3.list_buckets() as `junior` again -> expects success.
"""
import json
import os
import time

import boto3
from botocore.exceptions import ClientError

ENDPOINT = os.environ.get("FLOCI_ENDPOINT", "http://floci:4566")
USER = "junior"

admin_iam = boto3.client(
    "iam", endpoint_url=ENDPOINT, aws_access_key_id="test", aws_secret_access_key="test"
)


def ensure_user_and_key():
    try:
        admin_iam.create_user(UserName=USER)
    except admin_iam.exceptions.EntityAlreadyExistsException:
        pass

    key = admin_iam.create_access_key(UserName=USER)
    return key["AccessKey"]["AccessKeyId"], key["AccessKey"]["SecretAccessKey"]


def junior_s3_client(access_key, secret_key):
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )


def attach_allow_list_buckets_policy():
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Action": "s3:ListAllMyBuckets", "Resource": "*"}
        ],
    }
    admin_iam.put_user_policy(
        UserName=USER, PolicyName="AllowListBuckets", PolicyDocument=json.dumps(policy_doc)
    )


def main():
    print("Creating IAM user 'junior' and access key...")
    access_key, secret_key = ensure_user_and_key()
    s3_as_junior = junior_s3_client(access_key, secret_key)

    print("\nStep 1: list_buckets() as junior (no policy attached yet) -> expecting AccessDenied")
    try:
        s3_as_junior.list_buckets()
        print("UNEXPECTED SUCCESS — IAM enforcement may not be enabled "
              "(check FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true)")
    except ClientError as e:
        code = e.response["Error"].get("Code")
        message = e.response["Error"].get("Message")
        status = e.response["ResponseMetadata"].get("HTTPStatusCode")
        print(f"  -> {status} {code}: {message}")

    print("\nAttaching inline policy AllowListBuckets (s3:ListAllMyBuckets on *)...")
    attach_allow_list_buckets_policy()

    print("\nStep 2: list_buckets() as junior again -> expecting success")
    start = time.time()
    deadline = start + 30
    while time.time() < deadline:
        try:
            resp = s3_as_junior.list_buckets()
            elapsed = time.time() - start
            bucket_names = [b["Name"] for b in resp["Buckets"]]
            print(f"  -> SUCCESS after {elapsed:.2f}s, buckets: {bucket_names}")
            break
        except ClientError:
            time.sleep(1)
    else:
        raise SystemExit("Policy never took effect within 30s")


if __name__ == "__main__":
    main()
