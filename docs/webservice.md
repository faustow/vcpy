# Integrating `vcpy` into a webservice

If you want to create an Blockcerts-issuing web application with `vcpy` this document is for you.
We'll cover how to create a simple web service that issues 100% valid Blockcerts.
For this example we've chosen [cherrypy](https://github.com/cherrypy/cherrypy) because of its simplicity, but the same reasoning can be applied to any other web framework of course.

## Table of contents
1. [Issuing application](#issuing-application)
1. [Payload](#payload)
1. [Response](#response)


## Issuing application

The simplest possible web application that takes a JSON payload, processes it and produces valid Blockcerts could look like this:

```python
import cherrypy
from vcpy.components import Issuer, Assertion, EthereumAnchorHandler, Recipient
from vcpy.issue import BlockcertsBatch

class SampleIssuing(object):
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def issue(self):
        batch = BlockcertsBatch(
            issuer=Issuer(**cherrypy.request.json.get('issuer')),
            assertion=Assertion(**cherrypy.request.json.get('assertion')),
            recipients=[Recipient(**recipient_data) for recipient_data in cherrypy.request.json.get('recipients')],
            anchor_handler=EthereumAnchorHandler(**cherrypy.request.json.get('anchor_handler')),
        )
        tx_id, final_certs = batch.run()
        return [cert.to_dict() for cert in final_certs.values()]

cherrypy.quickstart(SampleIssuing())
```

To try this out, paste the above code into a `server.py` file and run `python server.py`. This should start the service in port `8080` of your localhost. (Please remember that this is an example only, this code should not be used in production environments)

## Payload

In order to trigger the issuing operation you need to send a POST request with a JSON payload to this service.
The following is an example `curl` call to this service that illustrates the endpoint and proper payload format:

```bash
curl -X POST \
  http://127.0.0.1:8080/issue \
  -H 'Content-Type: application/json' \
  -H 'Host: 127.0.0.1:8080' \
  -d '{
    "issuer": {
        "name": "Chalmers University of Technology",
        "url": "https://gist.githubusercontent.com/faustow/98db76b26b4d297d0eb98d499e733f77/raw/71f034f76d50fbe8656d6843d72ba1ed42581837/vc_issuer.json",
        "email": "info@chalmers.se",
        "image": "",
        "revocation_list": "https://gist.githubusercontent.com/faustow/07a66855d713409067ff28e10778e2dd/raw/e08bb6d6f1350367d3f6d4f805ab3b1466b584d7/revocation-list-testnet.json",
        "public_key": "0x472..."
    },
    "assertion": {
        "id": "2345678901",
        "name": "Automation and Mechatronics Engineer",
        "description": "https://www.pluggaz.se/",
        "image": "data:image/png;base64,iVBORw0KGgoAAAANS...",
        "narrative": "Candidates must be smart."
    },
    "recipients": [
        {
            "name": "Fausto Woelflin",
            "email": "fausto@dock.io",
            "public_key": "3456789012"
        },
        {
            "name": "Eddie Vedder",
            "email": "ed@pearljam.net",
            "public_key": "1456789012"
        }
    ],
    "anchor_handler": {
        "node_url": "https://ropsten.infura.io/v3/...",
        "public_key": "0x472...",
        "private_key": "...",
        "key_created_at": "2019-03-26T23:37:07.464654+00:00"
    }
}'
```
(Please note that sensitive or overly long fields have been truncated)

If you don't immediately get an error message it means that the payload was formatted properly. 

## Response 

After a few seconds, if you've sent a 100% valid payload, you should have a response JSON with two valid blockcerts, one for each recipient.
Let's look at the response from the above example:

```json
[
    {
        "@context": [
            "https://w3id.org/openbadges/v2",
            "https://w3id.org/blockcerts/v2",
            {
                "displayHtml": {
                    "@id": "schema:description"
                }
            }
        ],
        "type": "Assertion",
        "issuedOn": "2020-01-31T22:03:31.022630+00:00",
        "id": "urn:uuid:6b9e5c12-bdc9-4693-8ad6-b234a3e90971",
        "recipient": {
            "type": "email",
            "identity": "fausto@dock.io",
            "hashed": false
        },
        "recipientProfile": {
            "type": [
                "RecipientProfile",
                "Extension"
            ],
            "name": "Fausto Woelflin",
            "publicKey": "ecdsa-koblitz-pubkey:3456789012"
        },
        "badge": {
            "type": "BadgeClass",
            "id": "urn:uuid:2345678901",
            "name": "Automation and Mechatronics Engineer",
            "description": "https://www.pluggaz.se/",
            "image": "data:image/png;base64,iVBORw0KGgoAAAANS...",
            "issuer": {
                "id": "https://gist.githubusercontent.com/faustow/98db76b26b4d297d0eb98d499e733f77/raw/71f034f76d50fbe8656d6843d72ba1ed42581837/vc_issuer.json",
                "type": "Profile",
                "name": "Chalmers University of Technology",
                "url": "https://gist.githubusercontent.com/faustow/98db76b26b4d297d0eb98d499e733f77/raw/71f034f76d50fbe8656d6843d72ba1ed42581837/vc_issuer.json",
                "email": "info@chalmers.se",
                "image": "",
                "revocationList": "https://gist.githubusercontent.com/faustow/07a66855d713409067ff28e10778e2dd/raw/e08bb6d6f1350367d3f6d4f805ab3b1466b584d7/revocation-list-testnet.json"
            },
            "criteria": {
                "narrative": "Candidates must be smart."
            }
        },
        "verification": {
            "type": [
                "MerkleProofVerification2017",
                "Extension"
            ],
            "publicKey": "ecdsa-koblitz-pubkey:0x472..."
        },
        "signature": {
            "type": [
                "MerkleProof2017",
                "Extension"
            ],
            "merkleRoot": "4c41fab4606b4b558283e3b54f347a009b1017b7804e5a2a2379aab84ed2d4f1",
            "targetHash": "8177149e4e7ff9e2bd0dc88b6b360a164ec4790721474f7b4057a60eac0e8940",
            "proof": [
                {
                    "right": "5d75408a3fb9b2b5b6620e82241537930a1ee604e006cd9be740b301732437a0"
                }
            ],
            "anchors": [
                {
                    "sourceId": "0xb75fead8f27663dbf9ad4d38a521fdb65df9e86859229a3243ce000283527852",
                    "type": "ETHData",
                    "chain": "ethereumRopsten"
                }
            ]
        }
    },
    {
        "@context": [
            "https://w3id.org/openbadges/v2",
            "https://w3id.org/blockcerts/v2",
            {
                "displayHtml": {
                    "@id": "schema:description"
                }
            }
        ],
        "type": "Assertion",
        "issuedOn": "2020-01-31T22:03:31.022630+00:00",
        "id": "urn:uuid:aee51c7d-1b0d-4485-82ba-c42ce5e462e2",
        "recipient": {
            "type": "email",
            "identity": "ed@pearljam.net",
            "hashed": false
        },
        "recipientProfile": {
            "type": [
                "RecipientProfile",
                "Extension"
            ],
            "name": "Eddie Vedder",
            "publicKey": "ecdsa-koblitz-pubkey:1456789012"
        },
        "badge": {
            "type": "BadgeClass",
            "id": "urn:uuid:2345678901",
            "name": "Automation and Mechatronics Engineer",
            "description": "https://www.pluggaz.se/",
            "image": "data:image/png;base64,iVBORw0KGgoAAAANS...",
            "issuer": {
                "id": "https://gist.githubusercontent.com/faustow/98db76b26b4d297d0eb98d499e733f77/raw/71f034f76d50fbe8656d6843d72ba1ed42581837/vc_issuer.json",
                "type": "Profile",
                "name": "Chalmers University of Technology",
                "url": "https://gist.githubusercontent.com/faustow/98db76b26b4d297d0eb98d499e733f77/raw/71f034f76d50fbe8656d6843d72ba1ed42581837/vc_issuer.json",
                "email": "info@chalmers.se",
                "image": "",
                "revocationList": "https://gist.githubusercontent.com/faustow/07a66855d713409067ff28e10778e2dd/raw/e08bb6d6f1350367d3f6d4f805ab3b1466b584d7/revocation-list-testnet.json"
            },
            "criteria": {
                "narrative": "Candidates must be smart."
            }
        },
        "verification": {
            "type": [
                "MerkleProofVerification2017",
                "Extension"
            ],
            "publicKey": "ecdsa-koblitz-pubkey:0x472..."
        },
        "signature": {
            "type": [
                "MerkleProof2017",
                "Extension"
            ],
            "merkleRoot": "4c41fab4606b4b558283e3b54f347a009b1017b7804e5a2a2379aab84ed2d4f1",
            "targetHash": "5d75408a3fb9b2b5b6620e82241537930a1ee604e006cd9be740b301732437a0",
            "proof": [
                {
                    "left": "8177149e4e7ff9e2bd0dc88b6b360a164ec4790721474f7b4057a60eac0e8940"
                }
            ],
            "anchors": [
                {
                    "sourceId": "0xb75fead8f27663dbf9ad4d38a521fdb65df9e86859229a3243ce000283527852",
                    "type": "ETHData",
                    "chain": "ethereumRopsten"
                }
            ]
        }
    }
]
```
As you can see this reponse contains a list with two JSON objects. Each object is a valid blockcert anchored to the Ethereum blockchain (ropsten in this case). 