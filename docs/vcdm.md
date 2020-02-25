# Verifiable Claims Data Model v1 + Blockcerts v2


This section provides an overview at how a PoC of *"how wrapping a valid [Blockcert v2](https://www.blockcerts.org) with a valid [Verifiable Claim v1]((https://www.w3.org/TR/vc-data-model/)) can be achieved"*.


## Table of contents
1. [Disclaimer](#disclaimer)
1. [Prerequisites](#prerequisites)
1. [Combined Validation](#combined-validation)
1. [Combined Issuing](#combined-issuing)
1. [Bibliography](#bibliography)

## Disclaimer
Please note that this is only a PoC. Discussions are still taking place on the best way to approach this, but we wanted to share _one_ way of doing it.

## Prerequisites
- [vcpy](https://github.com/docknetwork/vcpy)
- [vc-demo](https://github.com/digitalbazaar/vc-demo) (please make sure to follow through the README to make sure you end up with a valid set of keys for VCDM signing.)

## Combined Validation

The verification process at a high level consists of two steps:
1. Validate the combined JSON file as "a valid VCDMv1 credential"
1. Extract the embedded Blockcert V2 and run the Blockcerts verification process on it. 

### Code
An example of a quick PoC implementation of such a combined verifier could look like follows:
```python
import json
import os
import subprocess
import sys

from cert_core import to_certificate_model
from cert_verifier.verifier import verify_certificate

PWD = os.path.dirname(os.path.abspath(__file__))


def run_cmd(cmd) -> str:
    """Run a command and return stdout."""
    try:
        output = subprocess.check_output(cmd, cwd=PWD, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        return e.output
    return output


def is_vcdm_valid(stdout) -> bool:
    response = json.loads(stdout)
    return response['verified']


def verify_vcdm(vcdm_file) -> bool:
    result = run_cmd(f'./vcdm_verify.sh {vcdm_file}')
    return is_vcdm_valid(result)


def get_blockcert_from_vcdm(vcdm_path) -> dict:
    with open(vcdm_path, 'r') as this_cert:
        vcdm1_cert = json.loads(this_cert.read())
        return vcdm1_cert['claim']


def verify_blockcert(blockcert_json):
    certificate_model = to_certificate_model(certificate_json=blockcert_json)
    result = verify_certificate(certificate_model)
    return result[-1]['status'] == 'passed'


def verify_vcdm_wrapped_blockcert(VCDM_FILE_PATH) -> dict:
    """Reads a vcdm-wrapped-blockcert file and runs both validations. Returns a dict with the results."""
    vcdm_verification_result = verify_vcdm(VCDM_FILE_PATH)
    blockcerts_verification_result = verify_blockcert(get_blockcert_from_vcdm(VCDM_FILE_PATH))
    return dict(
        vcdm_v1_verification=vcdm_verification_result,
        blockcerts_v2_verification=blockcerts_verification_result,
    )


if __name__ == "__main__":
    VCDM_FILE_PATH = sys.argv[1]
    validation_results = verify_vcdm_wrapped_blockcert(VCDM_FILE_PATH)
    print(' VCDM v1 + BLOCKCERTS v2 VERIFICATION '.center(80, '='))
    print(validation_results)

```
Saving this file as `combined_verifier.py` would allow you to run it as: 
`python combined_verifier.py some_combined_vcdm_v1_blockcerts_v2.jsonld`
which should yield something like this:
```bash
===================== VCDM v1 + BLOCKCERTS v2 VERIFICATION =====================
{'vcdm_v1_verification': True, 'blockcerts_v2_verification': True}
```

### Caveats
- The current version of `cert-verifier` does not provide useful enough error messages for development when things go wrong. Consider editing `cert_verifier/checks.py` there to add proper error messages to the `do_execute` functions in it.
- An additional file `vcdm_verify.sh` is used in this demo, this is just a convenience script that contains:
```bash
#!/usr/bin/env bash
docker run -i -v $(pwd):/home/node/app/key-file digitalbazaar/vc-js-cli verify < "$1"
```

## Combined Issuing

The combined issuing process at a high level consists of two steps:
1. Issue a valid blockcert 
1. Wrap it with a valid Verifiable Claim and sign it properly.

### Code
An example implementation for the above mentioned process could be approached like follows (for the purpose of a PoC, in a production environment the solution would have to differ): 
```python
import copy
import json
import os
import subprocess
from datetime import datetime

from attrdict import AttrDict

from verifiable_credentials.components import Issuer, Assertion, Recipient, EthereumAnchorHandler

SAMPLE_ISSUER = Issuer(
    name='Chalmers University of Technology',
    url='https://gist.githubusercontent.com/faustow/98db76b26b4d297d0eb98d499e733f77/raw/71f034f76d50fbe8656d6843d72ba1ed42581837/vc_issuer.json',
    email='info@chalmers.se',
    image='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="',
    revocation_list='https://gist.githubusercontent.com/faustow/07a66855d713409067ff28e10778e2dd/raw/e08bb6d6f1350367d3f6d4f805ab3b1466b584d7/revocation-list-testnet.json',
    public_key='0x472C1a6080a84694990BA2B9a29Ceef672c91d31',
    signature_name='Napoleon Dynamite',
    signature_job_title='President',
    signature_image='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="',
)

SAMPLE_ASSERTION = Assertion(
    id='2345678901',
    name='Automation and Mechatronics Engineer',
    description='https://www.pluggaz.se/',
    image='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="',
    narrative='Candidates must...',
)

SAMPLE_RECIPIENTS = [
    Recipient(
        name='Fausto Woelflin',
        email='fausto@dock.io',
        public_key='3456789012',
    ),
    Recipient(
        name='Eddie Vedder',
        email='ed@pearljam.net',
        public_key='4567890123',
    ),
    Recipient(
        name='Thomas Shellby',
        email='tom@shellbylimited.com',
        public_key='5678901234',
    ),
]

SAMPLE_ANCHOR_HANDLER = EthereumAnchorHandler(
    node_url='https://ropsten.infura.io/v3/b64e5fd4b1bd4a2b8ed44a32c547c5c7',
    public_key='0x472...',
    private_key='...',
    key_created_at='2019-03-26T23:37:07.464654+00:00',
)

SAMPLE_VCDM_JOB = AttrDict(
    dict(
        signing_key_file={
            "id": "https://gist.githubusercontent.com/faustow/13f43164c571cf839044b60661173935/raw",
            "controller": "https://gist.githubusercontent.com/faustow/3b48e353a9d5146e05a9c344e02c8c6f/raw",
            "type": "EcdsaSecp256k1VerificationKey2019",
            "privateKeyBase58": "...",
            "publicKeyBase58": "..."
        }
    )
)

VCDM_TEMPLATE = AttrDict({
    "@context": [
        "https://www.w3.org/2018/credentials/v1",
        "https://w3id.org/openbadges/v2",
        "https://gist.githubusercontent.com/faustow/3d6f830602f6d5d5fec02d2adcb0225c/raw/fdabbd02e85a83b72a4b771c43bd58ce0552e94f/blockcerts_v2_minus_proof_plus_chain.jsonld"
    ],
    "id": "",
    "type": [
        "VerifiableCredential",
        "Assertion"
    ],
    "issuer": "",
    "issuanceDate": "",
    "claim": {},
    "credentialSubject": ""
})

PWD = os.path.dirname(os.path.abspath(__file__))


def run_cmd(cmd) -> str:
    """Run a command and return stdout."""
    try:
        output = subprocess.check_output(cmd, cwd=PWD, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        return e.output
    return output


def vcdm_issue(key_file_contents, unsigned_vcdm) -> bool:
    """Writes the needed temporary files (key, unsigned vcdm) and finally calls vc issue with them."""
    key_file = 'my-key.json'
    id = unsigned_vcdm.id.split(':')[-1]
    with open(key_file, 'w') as keyfile:
        keyfile.write(json.dumps(key_file_contents))
    unsigned_file_path = f'combined_issuing_output/unsigned_vcdm_{id}.jsonld'
    signed_file_path = f'combined_issuing_output/signed_vcdm_{id}.jsonld'

    with open(unsigned_file_path, 'w') as thisfile:
        thisfile.write(json.dumps(unsigned_vcdm))
    command = f'./vcdm_issue.sh {key_file} {unsigned_file_path} {signed_file_path}'
    print(command)
    result = run_cmd(command)
    print(result)
    return result


def wrap_with_vcdm(blockcert) -> dict:
    """Wraps a blockcert witha VCDM v1"""
    CURRENT_DATETIME = datetime.utcnow().isoformat() + "+00:00"
    unsigned_vcdm = copy.deepcopy(VCDM_TEMPLATE)
    blockcert = AttrDict(blockcert)
    unsigned_vcdm.id = blockcert.id
    unsigned_vcdm.issuer = blockcert.badge.issuer.id
    unsigned_vcdm.issuanceDate = CURRENT_DATETIME
    unsigned_vcdm.claim = blockcert
    unsigned_vcdm.credentialSubject = blockcert.recipient
    return unsigned_vcdm


def combined_issuing(issuer, assertion, recipients, anchor_handler, vcdm_job):
    from verifiable_credentials import issue
    batch = issue.BlockcertsBatch(
        issuer=issuer,
        assertion=assertion,
        recipients=recipients,
        anchor_handler=anchor_handler,
    )
    tx_id, issued_blockcerts = batch.run()
    assert isinstance(issued_blockcerts, dict)
    assert len(issued_blockcerts.keys()) == 3

    for blockcert in issued_blockcerts.values():
        blockcert_dict = blockcert.to_dict()
        with open(f'combined_issuing_output/issued_blockcert_{blockcert_dict["id"]}.json', 'w') as thisfile:
            thisfile.write(json.dumps(blockcert_dict))

    unsigned_vcdms = []
    for blockcert in issued_blockcerts.values():
        unsigned_vcdm = wrap_with_vcdm(blockcert.to_dict())
        unsigned_vcdms.append(unsigned_vcdm)

    for unsigned_vcdm in unsigned_vcdms:
        vcdm_issue(vcdm_job['signing_key_file'], unsigned_vcdm)


if __name__ == "__main__":
    combined_issuing(SAMPLE_ISSUER, SAMPLE_ASSERTION, SAMPLE_RECIPIENTS, SAMPLE_ANCHOR_HANDLER, SAMPLE_VCDM_JOB)

```
Saving this file as `combined_issuer.py` would allow you to run it as `python combined_issuer.py`. The final `signed_vcdm_...` files will pass the `combined_verifier.py` checks.

### Caveats
- Sensitive information like the private keys have been removed from this demo, please enter your own if you want to run this.
- An additional file `vcdm_issue.sh` is used in this demo, it is just a convenience script with the following contents:
```bash
#!/usr/bin/env bash
docker run -i -v $(pwd):/home/node/app/key-file digitalbazaar/vc-js-cli issue --key "$1" < "$2" > "$3"
```

## Bibliography
- https://www.w3.org/TR/vc-data-model/
- https://github.com/WebOfTrustInfo/rwot6-santabarbara/blob/master/final-documents/open-badges-are-verifiable-credentials.pdf
- https://github.com/digitalbazaar/vc-demo
- https://github.com/blockchain-certificates/cert-verifier
- https://github.com/blockchain-certificates/cert-core