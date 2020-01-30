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


def test_issuing_with_images(issuer, assertion, recipients, eth_anchor_handler):
    image_b64_checkmark = "data:image/png;base64,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"
    title = "President"
    name = "John"

    issuer.image = image_b64_checkmark
    issuer.signature_image = image_b64_checkmark
    issuer.signature_job_title = title
    issuer.signature_name = name
    assertion.image = image_b64_checkmark

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
        this_cert = cert.to_dict()
        assert this_cert['badge']['image'] == image_b64_checkmark
        assert this_cert['badge']['issuer']['image'] == image_b64_checkmark
        assert this_cert['signatureLines'][0]['image'] == image_b64_checkmark
        assert this_cert['signatureLines'][0]['jobTitle'] == title
        assert this_cert['signatureLines'][0]['name'] == name
