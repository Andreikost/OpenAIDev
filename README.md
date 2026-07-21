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
evidence. The planned GPT-5.6
curriculum/explanation layer and camera input are deliberately not represented
as implemented features yet.

## Security

No credentials belong in this repository. VPS and OpenAI credentials must be
provided through local or server-side environment variables. Existing files
under `D:/GitHub/AI` are read-only references and must never be copied here if
they contain credentials or private infrastructure data.
