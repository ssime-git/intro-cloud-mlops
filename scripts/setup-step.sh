#!/bin/bash
# Recreates, on a fresh Floci and an empty lab/, what the tutorials before
# tutorial N left behind (the files you would have written in lab/, and the
# AWS resources), so tutorial N can be done (again) from its starting point.
# Run by `make reset-step` inside the work terminal.
set -euo pipefail
N=${1:?usage: setup-step.sh <tutorial number>}
say() { echo "  - $*"; }
mkdir -p lab

if [ "$N" -ge 2 ]; then   # tutorial 1: Alice and her policy
  cat > lab/list-buckets.json <<'JSON'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "s3:ListAllMyBuckets",
    "Resource": "*"
  }]
}
JSON
  aws iam create-user --user-name alice >/dev/null
  aws iam put-user-policy --user-name alice --policy-name list-buckets \
    --policy-document file://lab/list-buckets.json
  say "user alice with policy list-buckets (lab/list-buckets.json)"
fi

if [ "$N" -ge 3 ]; then   # tutorial 2: the SSH key pair
  rm -f lab/ml-key.pem
  aws ec2 create-key-pair --key-name ml-key --query KeyMaterial --output text > lab/ml-key.pem
  chmod 400 lab/ml-key.pem
  say "key pair ml-key (lab/ml-key.pem)"
fi

if [ "$N" -ge 4 ]; then   # tutorial 3: the bucket and its data, the EC2 role
  aws s3 mb s3://customers-data >/dev/null
  aws s3 cp data/customers.csv s3://customers-data/in/customers.csv >/dev/null
  python scoring/score.py data/customers.csv /tmp/out.csv >/dev/null
  aws s3 cp /tmp/out.csv s3://customers-data/out/customers.csv >/dev/null
  say "bucket customers-data with in/customers.csv and out/customers.csv"
  cat > lab/trust-ec2.json <<'JSON'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "ec2.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
JSON
  cat > lab/scoring-s3.json <<'JSON'
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::customers-data/in/*" },
    { "Effect": "Allow", "Action": "s3:PutObject", "Resource": "arn:aws:s3:::customers-data/out/*" }
  ]
}
JSON
  aws iam create-role --role-name scoring-ec2-role \
    --assume-role-policy-document file://lab/trust-ec2.json >/dev/null
  aws iam put-role-policy --role-name scoring-ec2-role --policy-name scoring-s3 \
    --policy-document file://lab/scoring-s3.json
  aws iam create-instance-profile --instance-profile-name scoring-ec2 >/dev/null
  aws iam add-role-to-instance-profile --instance-profile-name scoring-ec2 \
    --role-name scoring-ec2-role
  say "role scoring-ec2-role and instance profile scoring-ec2 (lab/trust-ec2.json, lab/scoring-s3.json)"
fi

if [ "$N" -ge 5 ]; then   # tutorial 4: the Lambda pipeline
  python pipeline/deploy.py >/dev/null
  aws s3 cp data/customers.csv s3://customers-data/in/day2.csv >/dev/null
  say "Lambda score wired to s3://customers-data/in/, in/day2.csv uploaded"
fi

echo "Ready for tutorial $N."
