# Threat Model

This document describes the trust assumptions, attack surface, and security boundaries of the Encrypted Inference API reference implementation.

It is meant to answer three questions clearly:

1. what the server can and cannot see
2. what kinds of adversaries the system is designed to resist
3. what threats are intentionally out of scope

This is a threat model for a **protocol-first reference implementation**, not a full production security guide.



## Security Goal

The primary security goal of this system is:

> allow a client to submit encrypted model inputs for inference without revealing plaintext inputs or client-side decryption secrets to the server.

More specifically, the design aims to ensure that:

- plaintext input features remain client-side
- secret decryption material remains client-side
- the server operates on ciphertexts rather than plaintext inputs
- malformed or incompatible encrypted inputs are rejected before evaluation
- protocol validation behavior is explicit rather than implicit



## Trust Boundaries

The system has two main trust domains:

- **Client / SDK**
- **Server / Reference Backend**

The boundary between them is the protocol wire contract defined by:

- JSON Schemas
- `openapi.yaml`
- documented validation invariants and error behavior

The client is trusted to:

- construct a compatible encryption session locally
- encrypt inputs correctly
- keep secret key material private
- submit well-formed requests

The server is trusted to:

- validate request envelopes before evaluation
- validate ciphertext structure and compatibility before evaluation
- execute the selected homomorphic model logic as implemented
- return encrypted results without requiring client secret material



## What the Server Can See

The server can see or infer at least the following:

- model identifiers and requested versions
- protocol metadata included in the request
- ciphertext payload bytes
- ciphertext size and shape information exposed by the request format
- batch size or request structure where explicitly provided
- request timing, frequency, and access patterns
- job identifiers and job polling behavior
- encrypted outputs produced by evaluation

The server also knows:

- the server-side model implementation
- model metadata published through discovery
- validation outcomes and rejection reasons produced at the protocol layer

This means the system does **not** hide all metadata. It protects plaintext inputs, not overall request observability.



## What the Server Cannot See

Under the intended design and assumptions, the server should not receive:

- plaintext input feature values
- the client secret key
- client-side decryption capability
- plaintext inference results after client decryption

The server operates on ciphertexts and returns ciphertext results. Decryption is intended to happen only on the client side.



## Protected Assets

The main assets the system is trying to protect are:

- client plaintext inputs
- client decryption key material
- correctness of protocol validation before encrypted evaluation
- separation between protocol contract and backend-specific cryptographic internals

A secondary asset is implementation conformance: the server should behave according to the published schemas and validation rules rather than relying on implicit assumptions.



## Adversary Model

This reference design mainly considers the following adversaries.

### 1. Honest-but-curious server operator

The server operator can inspect requests, ciphertext payloads, metadata, timing, and job behavior, but should not learn plaintext inputs solely from receiving encrypted requests.

This is the core privacy adversary the system is meant to address.

### 2. Malicious or careless client sending malformed inputs

A client may send:

- structurally invalid request payloads
- incompatible model identifiers
- ciphertexts with invalid or unexpected structure
- ciphertexts incompatible with advertised parameters
- oversized or adversarial payloads intended to trigger backend failures

The server is expected to reject such inputs before homomorphic evaluation whenever possible.

### 3. Network observer

A passive observer may see traffic volume, timing, endpoint usage, and payload sizes unless transport protections are deployed.

The protocol itself does not hide traffic metadata.

### 4. Integration or implementation drift

A client or server implementation may drift away from the published schemas or documented invariants.

The project addresses this through schema-based validation, OpenAPI documentation, and conformance testing.



## Main Attack Surface

The main attack surfaces are:

### `/models`

Potential issues:
- incorrect or incomplete model metadata
- metadata drift from actual backend requirements
- accidental coupling of discovery to backend internals

Security relevance:
- incorrect metadata can cause client/server incompatibility
- misleading metadata can cause invalid session construction

### `/infer`

This is the highest-risk endpoint.

Potential issues:
- malformed envelope payloads
- invalid model selection
- invalid batch structure
- malformed ciphertext bytes
- ciphertext/context incompatibility
- backend deserialization failures
- denial-of-service through oversized or adversarial inputs
- inconsistent runtime behavior compared with published schemas

Security relevance:
- this endpoint crosses directly into cryptographic and evaluation logic
- validation failures here must occur before evaluation whenever possible

### `/jobs/{id}`

Potential issues:
- exposure of job existence or state
- unauthorized result access in a multi-tenant deployment
- result enumeration if identifiers are guessable
- leakage through polling patterns

Security relevance:
- job/result retrieval must not undermine the privacy guarantees of encrypted submission



## Security Guarantees This Design Intends to Provide

The reference implementation is intended to provide these guarantees:

### Plaintext confidentiality from the server

The server should not need plaintext inputs or client decryption secrets to perform inference.

### Client-side key ownership

Secret decryption material is intended to remain client-side.

### Validation before evaluation

Malformed or incompatible requests should be rejected before homomorphic execution whenever possible.

### Explicit protocol contract

Schemas, endpoint shapes, and documented error behavior are part of the security story because ambiguity creates unsafe implementations.

### Backend abstraction boundary

Crypto-backend-specific logic should stay behind a defined abstraction rather than leaking into the protocol surface.



## Explicit Non-Guarantees

This repository does **not** guarantee:

- protection against all side-channel leakage
- hiding of traffic metadata, timing, or request volume
- production-grade denial-of-service resistance
- secure key generation UX or key distribution workflows
- hardened multi-tenant authorization by default
- resistance to a compromised client machine
- resistance to a compromised server host
- resistance to all cryptographic misuse outside the published protocol assumptions
- exact numeric equality after CKKS decryption

It also does not claim to provide a complete, formally verified production threat model.



## Out-of-Scope Threats

The following threats are explicitly outside the scope of the current reference implementation unless separately documented:

- operating system compromise on client or server
- memory scraping of client secret material on a compromised endpoint
- production secrets management and HSM integration
- deployment hardening, firewalling, and infrastructure isolation
- TLS termination and certificate management strategy
- large-scale abuse prevention and rate-limiting hardening
- tenant isolation guarantees for hosted multi-user deployments
- side-channel analysis of low-level cryptographic libraries
- malicious model definitions intentionally designed to leak information
- secure audit logging and forensic retention policy

These are important, but they are deployment and production concerns beyond the current scope.



## Assumptions

This threat model depends on the following assumptions:

- the client performs encryption locally
- the client retains exclusive control of decryption material
- the server does not require the client secret key
- model metadata accurately describes required encryption compatibility constraints
- the validation pipeline is executed before evaluation
- the cryptographic backend behaves according to its documented semantics
- the deployed environment provides whatever transport protection is required for the use case
- the reference implementation is used as a reference implementation, not mistaken for a hardened production service

If these assumptions do not hold, the security claims in this document weaken accordingly.



## Implementation Alignment

The current implementation is meant to align with this threat model in the following ways:

- model discovery is separated from local session construction
- encryption happens client-side in the SDK
- decryption happens client-side in the SDK
- `/infer` performs envelope validation before deeper crypto handling
- ciphertext validation occurs before homomorphic execution
- server-side logic operates on ciphertext-bearing payloads rather than plaintext features
- schemas and OpenAPI define the intended wire contract
- tests check conformance across SDK, server, and live round-trip behavior

## Residual Risk

Even when the system behaves as intended, residual risk remains from:

- metadata leakage through protocol-visible fields
- traffic analysis through timing and request size
- misuse or misconfiguration of cryptographic parameters
- incomplete validation coverage for adversarial ciphertexts
- implementation bugs in crypto libraries or backend glue code
- ambiguity between synchronous execution and job-based result semantics

These are known areas for future hardening.



## What Still Remains

The largest security documentation and hardening gaps are:

- stronger adversarial ciphertext hardening
- clearer documentation of metadata leakage
- clearer job/result authorization expectations
- fuller deployment-security guidance
- better documentation of transport-security assumptions
- more negative and adversarial end-to-end tests
- tighter conformance checks between schemas, OpenAPI, and runtime behavior



## Bottom Line

This system is designed to keep **plaintext inputs and decryption capability on the client side** while letting the server operate on ciphertexts under a strict protocol contract.

It should be understood as:

- a privacy-preserving encrypted inference reference design
- a protocol and validation artifact
- not a complete production security solution