import pytest

from verifiable_credentials import issue
from verifiable_credentials.components import Issuer, Assertion, Recipient


def test_issuing(issuer, assertion, recipients, eth_anchor_handler):
    batch = issue.BlockcertsBatch(
        issuer=issuer,
        assertion=assertion,
        recipients=recipients,
        anchor_handler=eth_anchor_handler,
    )
    tx_id, final_certs = batch.run()
    assert tx_id
    assert len(final_certs.keys()) == len(recipients)

    # import json
    # for id, cert in final_certs.items():
    #     with open(f"{id}.json", 'w') as this_cert_file:
    #         this_cert_file.write(json.dumps(cert.to_dict()))

    for cert in final_certs.values():
        assert cert.proof['anchors'][0]['sourceId'] == tx_id
        assert cert.proof['merkleRoot'] == batch.merkle_root
        assert not cert.expires_at


def test_empty_recipients(issuer, assertion, eth_anchor_handler):
    with pytest.raises(Exception) as excinfo:
        issue.BlockcertsBatch(
            issuer=issuer,
            assertion=assertion,
            recipients=[],
            anchor_handler=eth_anchor_handler,
        )
    assert "The field 'recipients' is required for object of class 'BlockcertsBatch'." in str(excinfo.value)


def test_issuing_expiration(issuer, assertion, recipients, eth_anchor_handler):
    expiration_date = "2018-02-07T23:52:16.636+00:00"
    batch = issue.BlockcertsBatch(
        issuer=issuer,
        assertion=assertion,
        recipients=recipients,
        anchor_handler=eth_anchor_handler,
        expires_at=expiration_date,
    )
    tx_id, final_certs = batch.run()
    assert tx_id
    assert len(final_certs.keys()) == len(recipients)
    for cert in final_certs.values():
        assert cert.expires_at == expiration_date
        assert cert.to_dict()['expires'] == expiration_date


def test_issuing_display_html(issuer, assertion, recipients, eth_anchor_handler):
    assertion.display_html = "<h1>Hello</h1>"
    batch = issue.BlockcertsBatch(
        issuer=issuer,
        assertion=assertion,
        recipients=recipients,
        anchor_handler=eth_anchor_handler,
    )
    tx_id, final_certs = batch.run()
    assert tx_id
    assert len(final_certs.keys()) == len(recipients)
    for cert in final_certs.values():
        assert cert.to_dict()["displayHtml"] == assertion.display_html


@pytest.mark.parametrize("missing_key", Issuer.REQUIRED_FIELDS)
def test_issuer_missing_fields(issuer, missing_key):
    issuer_dict = issuer.to_dict()
    issuer_dict[missing_key] = ""

    with pytest.raises(Exception) as excinfo:
        Issuer(**issuer_dict)
    assert f"The field '{missing_key}' is required for object of class 'Issuer'." in str(excinfo.value)


@pytest.mark.parametrize("missing_key", Assertion.REQUIRED_FIELDS)
def test_assertion_missing_fields(assertion, missing_key):
    assertion_dict = assertion.to_dict()
    assertion_dict[missing_key] = ""

    with pytest.raises(Exception) as excinfo:
        Assertion(**assertion_dict)
    assert f"The field '{missing_key}' is required for object of class 'Assertion'." in str(excinfo.value)


@pytest.mark.parametrize("missing_key", Recipient.REQUIRED_FIELDS)
def test_recipient_missing_fields(recipients, missing_key):
    recipient = recipients[0]
    recipient_dict = recipient.to_dict()
    recipient_dict[missing_key] = ""

    with pytest.raises(Exception) as excinfo:
        Recipient(**recipient_dict)
    assert f"The field '{missing_key}' is required for object of class 'Recipient'." in str(excinfo.value)
