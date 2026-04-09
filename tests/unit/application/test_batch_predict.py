from unittest.mock import patch

import numpy as np
import pandas as pd

from src.antifraud.application.batch_predict import run_batch

S3_UPLOAD = "src.antifraud.application.batch_predict.s3_upload"
S3_DOWNLOAD = "src.antifraud.application.batch_predict.s3_download"


def test_run_batch_execution(mocker, tmp_path):
    # Mocking external dependencies
    mocker.patch("src.antifraud.application.batch_predict.load_and_preprocess_data")
    mocker.patch("os.path.exists", return_value=True)

    # Mocking data loading
    mock_df = pd.DataFrame(
        {
            "Time": [1, 2],
            "Amount": [100, 200],
            "V1": [0.1, 0.2],
        }
    )
    mocker.patch(
        "src.antifraud.application.batch_predict.load_and_preprocess_data",
        return_value=mock_df,
    )

    # Mocking model
    mock_model = mocker.Mock()
    mock_model.feature_names_in_ = ["Time", "Amount", "V1"]
    mock_model.predict_proba.return_value = np.array([[0.9, 0.1], [0.2, 0.8]])

    mock_scaler = mocker.Mock()
    mock_scaler.transform.side_effect = lambda frame: frame
    mocker.patch(
        "src.antifraud.application.batch_predict.joblib.load",
        side_effect=[mock_model, mock_scaler],
    )

    output_file = tmp_path / "results.csv"

    with patch(S3_UPLOAD):
        run_batch("dummy_input.csv", str(output_file))

    # Check if output file was created
    assert output_file.exists()

    # Check results in dataframe
    result_df = pd.read_csv(output_file)
    assert "fraud_probability" in result_df.columns
    assert "is_fraud" in result_df.columns
