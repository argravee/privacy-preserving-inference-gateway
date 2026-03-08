# Encrypted Inference API (v0.9)

A protocol-first specification and reference implementation for privacy-preserving machine learning inference using homomorphic encryption.

## Overview

This project defines a versioned protocol for encrypted machine learning inference and provides a Python reference implementation of that protocol.

A client can:

1. discover supported models and their encryption requirements
2. construct a compatible CKKS context locally
3. encrypt input data on the client side
4. submit ciphertexts to the server
5. receive an encrypted inference result
6. decrypt the result locally

The server never needs the client’s secret key and never receives plaintext inputs.

This repository is focused on **protocol clarity, validation correctness, and implementation conformance**.

## Current Status

The repository currently includes:

- a versioned encrypted inference protocol
- JSON Schemas for request, response, and error payloads
- an OpenAPI 3.1 description of the HTTP surface
- a Python reference server
- a Python client/SDK
- a CKKS reference backend using Pyfhel
- automated tests across SDK, server, and live integration paths

A full live round-trip is working:

**discover model → build CKKS session → encrypt locally → submit ciphertext → server-side validate/evaluate → return ciphertext → decrypt locally**

This is a **reference implementation**, not a production deployment.


## Intended Audience

This specification is intended for:
- Engineers building privacy-preserving ML systems
- Researchers evaluating encrypted inference protocols
- Teams implementing compatible clients, servers, or SDKs

This repository aims to make encrypted inference easier to reason about and easier to implement correctly by emphasizing:

- protocol stability
- explicit structural contracts
- strict validation before evaluation
- clear separation between protocol and implementation details
- backend/client decoupling

## Non-Goals

This repository does **not** aim to:

- provide a production-ready serving platform
- train or fine-tune machine learning models
- handle key generation UX or key distribution workflows
- expose cryptographic internals such as noise budgets to clients
- guarantee exact decrypted numeric equality

Approximation error is expected under CKKS and is not treated as a protocol failure.

## High-Level Flow

1. Client calls `/models`
2. Client selects a supported model and reads its encryption requirements
3. Client constructs a compatible CKKS session locally
4. Client encrypts input features locally
5. Client submits an inference request to `/infer`
6. Server validates:
   - envelope shape
   - model/version identity
   - batch constraints
   - ciphertext structure and compatibility
7. Server performs homomorphic evaluation
8. Server stores and exposes the encrypted result via job/result flow
9. Client retrieves the result and decrypts locally

## Repository Structure
```
docs/
  api.md                      Human-readable protocol description
  api/examples/               Example protocol payloads

schemas/                      JSON Schemas for requests/responses/errors
openapi.yaml                  OpenAPI 3.1 protocol definition

server/
  app/                        FastAPI routes
  core/
    crypto/                   Crypto interfaces, CKKS backend, validation
    he_execution/             Homomorphic model execution
    jobs/                     Job state handling
    model_registry/           Model metadata loading and validation
    protocol/                 Envelope/schema validation
    security/                 Rate-limiting and tenant helpers

client/
  src/heapi_client/
    api.py                    Low-level HTTP wrapper
    client.py                 High-level SDK entry point
    discovery.py              Model discovery client
    infer.py                  Inference submission client
    jobs.py                   Job polling/waiting logic
    ckks/                     CKKS session and wire helpers

tests/
  sdk/                        SDK/unit tests
  server/                     Server/unit and route tests
  integration/                Live end-to-end protocol tests
  ```
## Protocol Artifacts
The normative protocol artifacts are:

* JSON Schemas
* `openapi.yaml`
* documented invariants and error semantics

These define the wire contract.

The reference backend is included to demonstrate one valid implementation of that contract.

## Reference Implementation Notes

The current reference implementation uses:

* **FastAPI** for the HTTP server
* **Pyfhel / CKKS** for encrypted arithmetic
* strict request and ciphertext validation before execution
* a Python SDK that performs local encryption and local decryption

The current design is intentionally conservative about validation and rejection behavior.

## Security Model

The intended security posture is:

* plaintext inputs remain client-side
* secret decryption material remains client-side
* server operates only on ciphertexts
* malformed or incompatible ciphertexts should be rejected before evaluation
* model requirements are explicit in metadata rather than implied

This repository is **not** a full production threat model or hardened deployment guide.

## Conformance

An implementation is considered protocol-compliant if it:

* accepts and emits payloads matching the published schemas
* implements the documented endpoints and response shapes
* preserves required validation semantics
* preserves documented error behavior at the protocol layer

Implementation details such as scheduling, persistence, or execution strategy are non-normative unless explicitly documented as part of the protocol.

## What Works Today

At the time of writing, the repository includes working support for:

* model discovery
* CKKS client session construction from model metadata
* local client encryption
* encrypted inference submission
* server-side ciphertext validation
* homomorphic evaluation for the reference logistic model
* encrypted result retrieval
* local client decryption
* automated SDK/server/integration testing

## What Still Remains

The major next-step areas are:

* stronger adversarial ciphertext hardening
* fuller threat-model documentation
* clearer architecture diagrams
* demo and onboarding material
* possible refinement of synchronous vs job-based execution semantics
* production-oriented persistence/queueing if the project evolves beyond reference scope

## Versioning

The protocol uses semantic versioning at the API/protocol level.

* breaking changes belong in a new major version
* v1.x changes should preserve the documented wire contract unless explicitly versioned otherwise


## License

Licensed under the Apache License, Version 2.0.
