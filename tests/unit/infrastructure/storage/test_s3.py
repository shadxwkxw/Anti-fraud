from unittest.mock import MagicMock, patch

from src.antifraud.infrastructure.storage import s3


def test_get_s3_client():
    with patch("src.antifraud.infrastructure.storage.s3.boto3") as b:
        s3.get_s3_client()
        b.client.assert_called_once()


def test_upload_model_default_key(tmp_path):
    f = tmp_path / "m.joblib"
    f.write_text("x")
    fake = MagicMock()
    with patch("src.antifraud.infrastructure.storage.s3.get_s3_client", return_value=fake):
        s3.upload_model(str(f))
    fake.upload_file.assert_called_once()


def test_upload_model_error():
    fake = MagicMock()
    fake.upload_file.side_effect = RuntimeError("boom")
    with patch("src.antifraud.infrastructure.storage.s3.get_s3_client", return_value=fake):
        s3.upload_model("/tmp/x", "key")


def test_download_model(tmp_path):
    fake = MagicMock()
    with patch("src.antifraud.infrastructure.storage.s3.get_s3_client", return_value=fake):
        s3.download_model("key", str(tmp_path / "sub" / "m.joblib"))
    fake.download_file.assert_called_once()


def test_download_model_error(tmp_path):
    fake = MagicMock()
    fake.download_file.side_effect = RuntimeError("boom")
    with patch("src.antifraud.infrastructure.storage.s3.get_s3_client", return_value=fake):
        s3.download_model("key", str(tmp_path / "m.joblib"))
