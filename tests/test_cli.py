from unittest.mock import patch
from types import SimpleNamespace
import kuristo.cli


@patch("kuristo.cli._batch.batch_submit")
def test_batch_calls_submit(mock_submit):
    args = SimpleNamespace(batch_command="submit", no_ansi=True)
    kuristo.cli.batch(args)
    mock_submit.assert_called_once_with(args)


@patch("kuristo.cli._batch.batch_status")
def test_batch_calls_status(mock_status):
    args = SimpleNamespace(batch_command="status", no_ansi=True)
    kuristo.cli.batch(args)
    mock_status.assert_called_once_with(args)
