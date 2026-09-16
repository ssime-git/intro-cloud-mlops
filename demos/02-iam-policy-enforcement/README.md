# Demo 2 — IAM policy enforcement

Demonstrates that Floci actually enforces IAM policies once enforcement is turned on.

## Prerequisites

Floci must be started with `FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true`. The `make demo2` target restarts the `floci` service with this flag automatically.

## Walkthrough

1. Using the admin credentials `test`/`test` (which bypass enforcement), reset the IAM user `junior` to a clean state (no policy, fresh access key).
2. Using `junior`'s keys, call `s3.list_buckets()` → expect **403 AccessDenied**.
3. Still as `test`/`test`, attach an inline policy allowing `s3:ListAllMyBuckets` on `*`.
4. Using `junior`'s keys again, call `s3.list_buckets()` → expect success.

## Run the demo

```bash
make up
make demo2
```

## Expected result

```
Step 1: list_buckets() as junior (no policy attached) -> expecting AccessDenied
  -> 403 AccessDenied: User is not authorized to perform: s3:ListAllMyBuckets

Attaching inline policy AllowListBuckets (s3:ListAllMyBuckets on *)...

Step 2: list_buckets() as junior again -> expecting success
  -> SUCCESS after 0.00s, buckets: []
```

## Teaching point

- Without `FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true`, **every** action is allowed regardless of the caller's identity — IAM enforcement is disabled by default.
- Policy propagation is instantaneous in Floci, unlike real AWS where a short propagation delay can be observed.
