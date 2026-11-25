#!/bin/bash
# User data: runs once, as root, when the instance boots.
# Installs the AWS CLI so the machine can talk to S3 itself.
set -e
dnf install -y -q awscli-2 > /var/log/install.log 2>&1

# CLI settings for root. cli_pager: print results straight to the terminal
# instead of opening `less` (easier to follow on screen).
# endpoint_url is Floci only: it sends the instance's AWS calls to the emulator
# instead of the real AWS endpoints. Remove it on a real EC2 instance.
mkdir -p /root/.aws
cat > /root/.aws/config <<'CFG'
[default]
region = us-east-1
cli_pager =
endpoint_url = http://floci:4566
CFG

echo "install.sh done" >> /var/log/install.log
