import numpy as np

from src.antifraud.domain.predictor import preprocess_single_tx


def test_preprocess_single_tx_returns_correct_columns(mocker):
    # Mocking model.feature_names_in_ and scaler.transform
    mock_scaler = mocker.Mock()
    mock_model = mocker.Mock()
    mocker.patch(
        "src.antifraud.domain.predictor.get_artifacts",
        return_value=(mock_model, mock_scaler),
    )

    mock_model.feature_names_in_ = np.array(["Time", "V1", "Amount", "hour", "is_night"])
    mock_scaler.transform.side_effect = lambda values: values

    test_data = {
        "Time": 3600.0,
        "V1": 1.0,
        "V2": 2.0,
        "Amount": 100.0,
    }

    result_df = preprocess_single_tx(test_data)

    # Check that only requested columns are present
    assert list(result_df.columns) == ["Time", "V1", "Amount", "hour", "is_night"]
    assert result_df["hour"].iloc[0] == 1
    assert result_df["is_night"].iloc[0] == 1


def test_preprocess_single_tx_handles_scaling(mocker):
    mock_scaler = mocker.Mock()
    mock_model = mocker.Mock()
    mocker.patch(
        "src.antifraud.domain.predictor.get_artifacts",
        return_value=(mock_model, mock_scaler),
    )

    mock_model.feature_names_in_ = np.array(["Amount"])
    # Scaler returns 0.5 for any input
    mock_scaler.transform.return_value = np.array([[0.5]])

    test_data = {"Time": 0, "Amount": 100.0}
    result_df = preprocess_single_tx(test_data)

    assert result_df["Amount"].iloc[0] == 0.5
