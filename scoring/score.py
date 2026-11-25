"""Scores a customers CSV: adds a `prediction` column (1 if score > 0.5 else 0).

The same `add_predictions()` runs on the laptop, on an EC2 instance and, from
step 4, inside the Lambda function. Only where it runs changes.

Standard library only, compatible with Python 3.9 (Amazon Linux 2023's python3).

Usage: python score.py customers.csv out.csv
"""
import csv
import io
import sys


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


def main(argv):
    if len(argv) != 3:
        sys.exit("usage: python score.py <input.csv> <output.csv>")
    src, dst = argv[1], argv[2]
    with open(src, encoding="utf-8") as f:
        result = add_predictions(f.read())
    with open(dst, "w", encoding="utf-8") as f:
        f.write(result)
    rows = result.count("\n") - 1
    print(f"scored {rows} rows: {src} -> {dst}")


if __name__ == "__main__":
    main(sys.argv)
