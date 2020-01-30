import pytest

from verifiable_credentials.components import EthereumAnchorHandler
from verifiable_credentials.issue import BlockcertsBatch


def test_missing_fields():
    with pytest.raises(Exception) as excinfo:
        BlockcertsBatch(issuer=None, assertion=None, recipients=None, anchor_handler=None)
    assert "is required for object of class 'BlockcertsBatch'." in str(excinfo.value)


def test_missing_fields_interactively(monkeypatch):
    with pytest.raises(OSError) as excinfo:
        EthereumAnchorHandler(node_url="", public_key="", private_key="", key_created_at="")
    assert "reading from stdin while output is captured!" in str(excinfo.value)

    monkeypatch.setattr('builtins.input', lambda prompt: "")
    with pytest.raises(Exception) as excinfo:
        EthereumAnchorHandler(node_url="", public_key="", private_key="", key_created_at="")
    assert "is missing even after asking for user input, for object of class 'EthereumAnchorHandler'." in str(
        excinfo.value)

    monkeypatch.setattr('builtins.input', lambda prompt: "some_value")
    EthereumAnchorHandler(node_url="", public_key="", private_key="", key_created_at="")
