import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).parent.parent / "demos" / "01-s3-lambda-notification" / "lambda_predict")
)

from handler import add_predictions  # noqa: E402


def test_add_predictions_thresholds_correctly():
    result = add_predictions("score\n0.9\n0.2\n0.7\n0.5\n")
    assert result == "score,prediction\n0.9,1\n0.2,0\n0.7,1\n0.5,0\n"


def test_add_predictions_preserves_extra_columns():
    result = add_predictions("id,score\na,0.6\nb,0.4\n")
    assert result == "id,score,prediction\na,0.6,1\nb,0.4,0\n"
