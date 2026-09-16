# Demo 1 — S3 → Lambda notification

A Python 3.12 Lambda (`predict`) is automatically triggered by an S3 notification when an object is created under the `in/` prefix of the `demo` bucket. It reads the CSV, adds a `prediction` column (`1` if `score > 0.5`, else `0`), and writes the result under `out/` with the same file name.

## Resources created

- IAM role `lambda-exec-role` (trust policy `lambda.amazonaws.com`), with an inline policy scoped to S3 read on `demo/in/*`, S3 write on `demo/out/*`, and CloudWatch Logs
- Lambda function `predict` (runtime `python3.12`, zip, 60s timeout)
- S3 bucket `demo`
- Lambda permission `lambda:InvokeFunction` for the `s3.amazonaws.com` principal
- S3 notification `s3:ObjectCreated:*` filtered on the `in/` prefix

## Run the demo

```bash
make up
make demo1
```

Manual equivalent:

```bash
docker compose exec -T runner python demos/01-s3-lambda-notification/deploy.py
docker compose exec -T runner python demos/01-s3-lambda-notification/trigger_and_wait.py
```

## Expected result

```
score,prediction
0.9,1
0.2,0
0.7,1
```

Typical delay observed: ~30s on the first trigger (downloading the `public.ecr.aws/lambda/python:3.12` runtime image), much faster afterwards.
