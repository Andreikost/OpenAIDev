# ColonyMind

[Live demo](https://openaidev.automationfreelancer.com) ·
[Submission evidence](docs/evidence/five-seed-baseline-2026-07-21.json) ·
[Build Week scope](docs/BUILD_WEEK_SCOPE.md) ·
[MIT license](LICENSE)

ColonyMind is a self-organizing vision architecture that learns from unlabeled
visual information while accounting for the computational resources used by
its cells, organism networks, and colonies.

Basic geometric shapes are the initial controlled benchmark, not the final
destination. The long-term direction is resource-aware learning for more
complex visual patterns and eventually opt-in camera streams.

The public demo runs anonymously with generated synthetic data. Google login is
optional and only makes versioned experiment history persistent.

## Judge test path

No rebuild or account is required. Open the live demo, let the retinal stream
advance, and use the traffic light to see whether unfamiliar information is
still feeding structural growth. Rotate and zoom the 3D architecture, select an
organism to inspect only its label, draw a shape in Draw & Audit, then run the
hidden-label evaluation and GPT-5.6 Research Auditor. From the resulting audit,
create a versioned experiment; it runs in a fresh engine while Baseline v1 stays
locked. Anonymous versions intentionally disappear on refresh.

## Project package

- [Implementation prompt](prompts/colonymind-implementation.prompt.json)
- [Project brief](docs/project-brief.md)
- [Devpost story](docs/devpost/project-story.md)
- [Devpost submission checklist](docs/devpost/submission-checklist.md)
- [Build Week scope](docs/BUILD_WEEK_SCOPE.md)
- [Repository and deployment workflow](docs/workflow.md)
- [P1 lifecycle benchmark](docs/experiments/p1-lifecycle-benchmark.md)
- [Open-ended growth benchmark](docs/experiments/open-ended-growth.md)
- [Micro-signature layer benchmark](docs/experiments/micro-signature-layer.md)
- [3D living architecture](docs/architecture/3d-living-architecture.md)
- [GPT-5.6 Research Auditor](docs/architecture/gpt-research-auditor.md)
- [Versioned Experiment Studio](docs/architecture/versioned-experiment-studio.md)
- [Devpost thumbnail](assets/colonymind-devpost-thumbnail.png)

## Run the benchmark locally

The first implementation is a deterministic, unlabeled geometric benchmark.
It starts with zero learned structure; training grows cells and organisms only
when a residual or novel visual regime warrants the resource cost.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pytest
.\.venv\Scripts\python.exe -m pytest app/tests -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8201
```

In a second terminal:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. Docker Compose serves the same application on
`http://127.0.0.1:8200` for the VPS release.

Supported development platforms are Windows, macOS, and Linux with Python
3.12+, Node.js 22+, and npm. Docker 24+ with Compose is the recommended
production path. No sample-data download is required: every retinal stimulus
and held-out evaluation sample is generated deterministically from a declared
seed.

Run the complete verification suite with:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest app/tests -q
cd ..\frontend
npm.cmd ci
npm.cmd run build
```

## Current status

The current open-ended memory build includes the geometry generator, label-free
feature learning, dynamic organisms, colony formation, resource proxies,
deterministic state hashes, global organism aging, maturation, low-compute
dormancy, similarity-triggered reactivation, conservative evidence-based archival,
growth without fixed population or cell-count ceilings, local cell competition,
information-food gating, a rotation-tolerant intermediate layer of local
micro-signatures and coactivation colonies, persistent fine-detail-driven concept
growth, and label-free consolidated community memories,
hidden-label read-only evaluation, a draw-your-own retinal probe with an external
geometric auditor, read-only ablation, and a downloadable JSON performance
report v5 with structural-change, intermediate-layer, digestion, memory, and audit
evidence. The browser visualizes the same live state as an interactive 3D field
with navigable cells, organisms, colony membranes, and memory engrams.

The external GPT-5.6 Research Auditor receives a compact, frozen JSON snapshot
of aggregate evidence and returns a schema-validated scientific interpretation:
findings, risks, controlled next experiments, and publication readiness. It has
no tools, learning write path, raw retinal pixels, or cell prototypes. Snapshot
hashes before and after extraction make this boundary visible in the interface.
Camera input remains a future phase and is not represented as implemented.

The Versioned Experiment Studio converts a cached auditor diagnosis into a
schema-validated protocol and runs it in fresh, isolated engines. The submitted
learner is an immutable baseline: GPT-5.6 cannot edit its code or parameters.
Anonymous versions live only for the current page lifetime; Google-authenticated
versions, instructions, lineage, status, and results persist in PostgreSQL.

## GPT-5.6 Research Auditor

Set `OPENAI_API_KEY` only in the backend environment. Optional settings are
`OPENAI_MODEL=gpt-5.6-sol` and `OPENAI_REASONING_EFFORT=medium`. The browser never
receives the credential. Repeated audits of the same state hash reuse a bounded
server-side cache rather than creating another API request.

Persistent experiment workspaces additionally require `DATABASE_URL`,
`GOOGLE_CLIENT_ID`, and `AUTH_JWT_SECRET` in the backend environment. Google
access tokens are verified server-side for the configured client audience; the
application then issues a seven-day, app-specific session token.

## How Codex and GPT-5.6 shaped the project

ColonyMind was built collaboratively in Codex during OpenAI Build Week. The
human entrant set the research direction and made the consequential product and
scientific decisions: reinterpret information as food, make organisms long
lived, remove fixed growth ceilings, introduce a fine-detail micro-signature
layer after observing circle/square confusion, preserve the submitted learner
as an immutable baseline, and require every derived experiment to be isolated
and reproducible.

Codex accelerated the implementation by inspecting the earlier Experiment 6
conceptual reference, designing the Python/NumPy vertical slice, adding the
64×64 retina and label boundary, implementing lifecycle and memory evidence,
building the React and Three.js inspection experience, writing regression and
API tests, interpreting exported run reports, integrating PostgreSQL and Google
login, creating the deployment workflow, and repeatedly verifying the public
VPS. Dated commits from July 18–21 document that progression.

GPT-5.6 has two deliberately bounded runtime roles through the OpenAI Responses
API and Structured Outputs:

1. A read-only Research Auditor interprets a frozen aggregate snapshot and
   proposes controlled next experiments. It receives no raw retina, prototypes,
   tools, or learning write path.
2. An Experiment Designer translates the audit plus optional human instructions
   into a Pydantic-validated, allowlisted protocol. It cannot edit the baseline
   or execute generated code; versions run in fresh engines.

This separation is a key engineering decision: Codex helped build and test the
system, GPT-5.6 challenges the evidence at runtime, and the learner remains the
subject of the experiment rather than being silently rewritten by the model.

## Reproducible submission result

The checked-in five-seed benchmark trains the immutable baseline for 240 steps
per seed and evaluates 72 balanced hidden-label samples per seed. It reports
purity 1.000 across all five seeds, mean NMI 0.9699, mean ARI 0.9641, and mean
fragmentation 1.2. All evaluator state hashes were preserved. These results are
limited to synthetic circles, triangles, and squares; they do not establish
natural-image or camera-vision performance. See the complete machine-readable
[evidence file](docs/evidence/five-seed-baseline-2026-07-21.json).

## Security

No credentials belong in this repository. VPS and OpenAI credentials must be
provided through local or server-side environment variables. Existing files
under `D:/GitHub/AI` are read-only references and must never be copied here if
they contain credentials or private infrastructure data.

Anonymous GPT-5.6 audits are protected by a bounded cache, a per-session
cooldown, a shared hourly allowance, and a concurrency limit. The backend uses
a separate 120-second auditor timeout and bounded output so an upstream delay
cannot trigger overlapping paid attempts. Third-party components and licenses
are documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
The optional authenticated demo data policy is documented in
[PRIVACY.md](PRIVACY.md).
