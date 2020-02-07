# vcpy

vcpy is an easy-to-use Python library to issue verifiable credentials. 

There are many kinds of verifiable credentials like W3C's Verifiable Claims, Blockcerts, and others. The goal of `vcpy` is to allow you to easily issue these from your own application!

*Note: this is a WIP, currently only Blockcerts issuing with anchoring to the Ethereum network is provided.*  
    
## Table of contents

1. [Why](#Why)
1. [Status](#Status)
1. [How to issue Blockcerts](how_to.md)
1. [Integrating `vcpy` into a web service](webservice.md)


## Why 
Although useful as PoCs, current implementations of verifiable credentials-issuing software projects suffer one or more of the following issues: 
- race conditions
- imposibility to use as part of a larger application
- overengineered code that makes it hard to contribute to

`vcpy` tries to improve user adoption by providing a better user experience, and to encourage open source contributions by using simpler code and good documentation.
Because Clean Code is better than fancy code.


## Status
- [x] Blockcerts issuing: 
  - [x] Batch issuing
  - [x] Anchor to Ethereum blockchain
- [ ] Blockcerts addons
  - [ ] Anchor to Bitcoin, Polkadot or other blockchains
  - [ ] Additional global fields
  - [ ] Additional per-recipient fields
- [ ] VCDMv1 issuing
  - [x] PoC example
  - [ ] Blockcerts-wrapping
  - [ ] Credential signing
- [ ] Remote schema validation ?
- [ ] More tests
