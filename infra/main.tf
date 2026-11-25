# The fourth way to talk to AWS: describe the state you want, and let
# Terraform work out the steps. The bucket and the EC2 role of step 3,
# reusing the policy files written by hand in lab/ during the tutorials.
#
# Shown on screen only: not applied during the masterclass.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "data" {
  bucket = "customers-data"
}

resource "aws_iam_role" "scoring" {
  name               = "scoring-ec2-role"
  assume_role_policy = file("${path.module}/../lab/trust-ec2.json")
}

resource "aws_iam_role_policy" "scoring_s3" {
  name   = "scoring-s3"
  role   = aws_iam_role.scoring.id
  policy = file("${path.module}/../lab/scoring-s3.json")
}
