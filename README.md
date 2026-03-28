![CI](https://github.com/argravee/encrypted-inference-api/actions/workflows/ci.yml/badge.svg)
![coverage](https://img.shields.io/badge/coverage-92%25-brightgreen)
![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)


# Privacy-Preserving Inference Gateway (v1.0.0)

A privacy-preserving inference gateway and reference implementation for machine learning inference that supports both a plaintext baseline path and a CKKS-based encrypted inference path.

The system allows a client to discover supported models, construct a compatible CKKS session locally, encrypt inputs on the client side, submit ciphertexts to the server, retrieve encrypted inference results, and decrypt outputs locally. The server never receives plaintext inputs or the client’s secret key.

This repository focuses on protocol clarity, validation correctness, implementation conformance, and measurable privacy-performance tradeoffs between plaintext and encrypted inference.

## Motivation

Encrypted inference systems can become ambiguous: protocol rules get mixed with backend details, validation becomes implicit, and clients become tightly coupled to a single implementation. This project instead defines a versioned wire contract first, then provides a Python reference implementation that demonstrates one valid way to satisfy that contract.

The goal is to make encrypted inference easier to reason about, easier to test, and easier to implement correctly.

## Intended Audience

This project is intended for:

* engineers building privacy-preserving ML systems
* researchers evaluating encrypted inference protocols
* teams implementing compatible clients, servers, or SDKs

## At a Glance

The client is responsible for:

- discovering model metadata
- constructing a compatible CKKS session locally
- encrypting input data locally
- submitting ciphertexts
- retrieving encrypted results
- decrypting results locally

The server is responsible for:

- exposing the protocol endpoints
- validating request envelopes
- validating ciphertext structure and compatibility
- performing homomorphic evaluation
- storing and returning encrypted results
  
## Benchmark Highlights

For the reference `logistic_v1` model (`8` input features, `20` measured runs), the plaintext and encrypted inference paths have a direct benchmark comparison:

- **Plaintext mean latency:** `3.78 ms`
- **Encrypted mean end-to-end latency:** `380.62 ms`
- **Plaintext throughput:** `264.77 req/s`
- **Encrypted throughput:** `2.63 req/s`
- **Plaintext request size:** `87 B`
- **Encrypted request size:** `12,585,046 B`
- **Mean absolute error:** `2.52e-6`
- **Max absolute error:** `5.53e-6`
  
See [`docs/benchmarking.md`](docs/benchmarking.md) for methodology, and [`docs/benchmark_results.md`](docs/benchmark_results.md) for charts, raw metrics, and interpretation.

## Architecture

```mermaid
flowchart LR

    subgraph CLIENT["Client / SDK"]
        direction TB
        C1["Discovery Client<br/>GET /models"]
        C2["Model Metadata"]
        C3["CKKS Session Builder"]
        C4["Local Encryption"]
        C5["Inference Submitter<br/>POST /infer"]
        C6["Jobs Client<br/>GET /jobs/{id}"]
        C7["Local Decryption"]
    end

    subgraph SERVER["Server / Reference Backend"]
        direction TB
        S1["/models Route"]
        S2["/infer Route"]
        S3["/jobs/{id} Route"]
        S4["Model Registry"]
        S5["Envelope Validation"]
        S6["Ciphertext Validation"]
        S7["CKKS Backend"]
        S8["HE Execution"]
        S9["Job Store"]
    end

    C1 --> S1
    S1 --> S4
    S4 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> C5

    C5 --> S2
    S2 --> S5
    S5 --> S4
    S5 --> S6
    S6 --> S7
    S7 --> S8
    S8 --> S9

    C6 --> S3
    S3 --> S9
    S9 --> C7
````

A more detailed description is available at [`architecture.md`](docs/architecture/architecture.md).

## Quick Start

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows PowerShell**

```bash
.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the reference server

```bash
uvicorn server.app.main:app --reload
```

The server will start at:

```txt
http://127.0.0.1:8000
```

### 4. Run tests

```bash
pytest
```

For live integration tests:

```bash
pytest tests/integration -v
```

## High-Level Flow

1. Client calls `/models`
2. Client selects a supported model and reads its encryption requirements
3. Client constructs a compatible CKKS session locally
4. Client encrypts input features locally
5. Client submits an inference request to `/infer`
6. Server validates the request envelope, model identity, constraints, and ciphertext compatibility
7. Server performs homomorphic evaluation
8. Server stores the encrypted result in job state
9. Client retrieves the encrypted result and decrypts locally

## Repository Structure

```text
benchmarks/
├── benchmark_inference.py        Benchmark harness
├── generate_report_assets.py     Static chart generator
└── results/                      Raw benchmark outputs

docs/
├── api/examples/                 Example protocol payloads
├── api.md                        Human-readable protocol description
├── architecture/architecture.md  Detailed architecture notes
├── benchmarking.md               Benchmark methodology + results
└── assets/                       Generated charts + diagrams

schemas/                          JSON Schemas (requests/responses/errors)
openapi.yaml                      OpenAPI 3.1 protocol definition

server/
├── app/
│   └── routes/                   FastAPI route handlers
├── core/
│   ├── crypto/
│   │   └── crypto_backends/
│   │       └── ckks_pyfhel/      Pyfhel CKKS backend implementation
│   ├── he_execution/             Homomorphic model execution
│   ├── plain_execution/          Plaintext execution (testing/debug)
│   ├── jobs/                     Job lifecycle + queue management
│   ├── model_registry/           Model metadata loading/validation
│   ├── protocol/                 Envelope + schema validation
│   └── security/                 Rate limiting + tenant helpers

client/
├── examples/                     Example client usage
└── src/heapi_client/
    ├── api.py                    Low-level HTTP wrapper
    ├── client.py                 High-level SDK entry point
    ├── discovery.py              Model discovery client
    ├── infer.py                  Inference submission client
    ├── jobs.py                   Job polling/waiting logic
    └── ckks/                     CKKS session + wire helpers

tests/
├── sdk/                          SDK/unit tests
├── server/                       Server/unit + route tests
├── integration/                  End-to-end protocol tests
└── plain/                        Plain execution tests

notebooks/                        Demo + E2E walkthroughs
```
## Current Artifacts

- Formal JSON Schemas and OpenAPI protocol contract
- Encrypted inference route with ciphertext validation
- Plaintext baseline inference route
- Python client-side encryption/decryption workflow
- Plaintext vs encrypted agreement tests
- Reproducible benchmark harness and result artifacts
- Benchmark report and static visual results page

## Protocol Artifacts

The normative protocol artifacts are:

* JSON Schemas
* `openapi.yaml`
* documented invariants and error semantics

These define the wire contract.

The reference backend is included to demonstrate one valid implementation of that contract.

## Current Status

The repository currently includes:

* a versioned encrypted inference protocol
* JSON Schemas and an OpenAPI 3.1 contract
* a Python reference gateway/server
* a Python client SDK
* a CKKS reference backend using Pyfhel
* a plaintext baseline inference path
* plaintext vs encrypted agreement testing
* reproducible benchmark tooling and result documentation

A full live round-trip is working:

**discover model → build CKKS session → encrypt locally → submit ciphertext → validate and evaluate server-side → retrieve ciphertext result → decrypt locally**

The repository also supports side-by-side plaintext vs encrypted benchmarking for the reference model.

## Security Model

The intended security posture is:

* plaintext inputs remain client-side
* secret decryption material remains client-side
* server operates only on ciphertexts
* malformed or incompatible ciphertexts should be rejected before evaluation
* model requirements are explicit in metadata rather than implied

This repository is not a hardened production deployment guide. See [`docs/threat-model.md`](docs/threat-model.md) for the current threat model and assumptions.

## Non-Goals

This repository does not aim to:

* provide a production-ready serving platform
* train or fine-tune machine learning models
* handle key generation UX or key distribution workflows
* expose cryptographic internals such as noise budgets to clients
* guarantee exact decrypted numeric equality

Approximation error is expected under CKKS and is not treated as a protocol failure.

## Conformance

An implementation is considered protocol-compliant if it:

* accepts and emits payloads matching the published schemas
* implements the documented endpoints and response shapes
* preserves required validation semantics
* preserves documented error behavior at the protocol layer

Implementation details such as scheduling, persistence, or execution strategy are non-normative unless explicitly documented as part of the protocol.

## V1+ Goals

The major next-step areas are:

* stronger adversarial ciphertext hardening
* refinement of synchronous versus job-based execution semantics
* production-oriented persistence and queueing 

## Versioning

The protocol uses semantic versioning at the API/protocol level.

* breaking changes belong in a new major version
* minor versions should preserve the documented wire contract unless explicitly versioned otherwise

## License

Licensed under the Apache License, Version 2.0.




