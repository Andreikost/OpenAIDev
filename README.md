# ColonyMind

ColonyMind is a self-organizing vision architecture that learns from unlabeled
visual information while accounting for the computational resources used by
its cells, organism networks, and colonies.

Basic geometric shapes are the initial controlled benchmark, not the final
destination. The long-term direction is resource-aware learning for more
complex visual patterns and eventually opt-in camera streams.

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
npm.cmd install
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. Docker Compose serves the same application on
`http://127.0.0.1:8200` for the VPS release.

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

## Security

No credentials belong in this repository. VPS and OpenAI credentials must be
provided through local or server-side environment variables. Existing files
under `D:/GitHub/AI` are read-only references and must never be copied here if
they contain credentials or private infrastructure data.
