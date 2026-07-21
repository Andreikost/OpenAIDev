# ColonyMind — final Devpost submission

## General information

- **Project name:** ColonyMind
- **Category:** Developer Tools
- **Elevator pitch:** A living visual learner that grows only while information remains undigested—and lets GPT-5.6 audit and version the evidence.
- **Live demo:** https://openaidev.automationfreelancer.com
- **Repository:** https://github.com/Andreikost/OpenAIDev
- **License:** MIT

## Built with

Codex, GPT-5.6, OpenAI Responses API, Structured Outputs, React, TypeScript,
Three.js, Vite, Python, FastAPI, NumPy, Pydantic, PostgreSQL, Docker, Pytest,
HTML5 Canvas, Unsupervised Learning, Dynamic Neural Networks, Bio-inspired AI.

## Judge testing instructions

1. Open the live demo in a private browser window. No account is required.
2. Let the retinal stream train the baseline and inspect the digestion traffic
   light, organisms, cells, micro-signatures, colonies, and persistent memories.
3. Rotate and zoom the 3D field. Click one organism to reveal only its label and
   lineage details.
4. Draw a circle, triangle, or square in Draw & Audit and compare the learner's
   community with the independent geometric auditor.
5. Run the frozen hidden-label evaluation, then click **Audit run**. The GPT-5.6
   result should show matching before/after state hashes and no learning write
   access.
6. Use Versioned Experiment Studio to create and run an isolated protocol. The
   immutable Baseline v1 remains locked. Anonymous versions disappear on refresh.

## Installation, supported platforms, and testing

**Fastest judge path — no installation or account required:** Open
https://openaidev.automationfreelancer.com in a current desktop version of
Chrome, Edge, Firefox, or Safari. Let the retinal stream advance; inspect the
learning traffic light; rotate, zoom, and select an organism in the 3D field;
draw a circle, triangle, or square in Draw & Audit; reveal the frozen
hidden-label evaluation; run the GPT-5.6 Research Auditor; and create an isolated
versioned experiment. Baseline v1 always remains locked. Anonymous experiment
versions intentionally disappear when the page is refreshed.

**Local installation:** Requires Git, Python 3.12+, Node.js 22+, and npm on
Windows, macOS, or Linux.

```bash
git clone https://github.com/Andreikost/OpenAIDev.git
cd OpenAIDev/backend
python -m venv .venv
# Activate .venv, then:
python -m pip install -r requirements.txt pytest
python -m uvicorn app.main:app --port 8201
```

In a second terminal:

```bash
cd OpenAIDev/frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. All retinal and held-out samples are generated
deterministically, so no dataset download is required. Run backend tests with
`python -m pytest app/tests -q` and verify the frontend with `npm run build`.
Docker 24+ with Compose is the recommended production path (`docker compose up
--build`, then open http://127.0.0.1:8200).

The core learner and local evaluation need no API key. The external Research
Auditor and Experiment Designer require a server-side `OPENAI_API_KEY`; the key
is never sent to the browser. Google login and PostgreSQL are optional and only
provide persistent experiment history; anonymous use remains fully available.

## Private judge access field

Live project: https://openaidev.automationfreelancer.com

No credentials or installation are required. Please use a current desktop
browser. Suggested 2–3 minute test: (1) let the retinal stream advance and watch
the learning traffic light; (2) rotate/zoom the Living Architecture 3D view and
select an organism; (3) draw a circle, triangle, or square in Draw & Audit; (4)
reveal the frozen hidden-label evaluation; (5) run the GPT-5.6 Research Auditor;
and (6) create an isolated experiment in Versioned Experiment Studio. Baseline
v1 is immutable. Anonymous experiment versions intentionally disappear on page
refresh; Google login is optional and only enables persistent history.

Source and reproducibility evidence:
https://github.com/Andreikost/OpenAIDev

## Required manual fields

- **YouTube demo URL:** `[PASTE PUBLIC YOUTUBE URL]`
- **Codex `/feedback` Session ID:** `[PASTE PRIMARY BUILD THREAD SESSION ID]`
- **Team:** Ensure every listed teammate has accepted the Devpost invitation.
- **Submission state:** Confirm the project displays **Submitted**, not Draft.

## Demo video script — target 2:50

### 0:00–0:18 — Problem and idea

“Most visual learners begin with a fixed architecture. ColonyMind asks a
different question: what if a learner could grow only while information remains
undigested, then consolidate familiar patterns into memory?”

Show the title, retina, and zero/early-growth state.

### 0:18–0:52 — Living learner

“Unlabeled circles, triangles, and squares arrive through a 64 by 64 retina with
rotation, scale, translation, noise, occlusion, and filled or outline rendering.
Residual information becomes food. The learner grows cells, small organism
networks, fine-detail micro-signatures, and colonies only when the evidence
justifies more structure.”

Show retina variations, the traffic light, then rotate and zoom the 3D field.

### 0:52–1:18 — Inspectability

“Every biological metaphor maps to a measurable mechanism. Cells are learned
prototypes, organisms are compact experts, colonies are cooperation, and green
engrams are consolidated memory. The visualization reads the live engine state;
it is not a prerecorded animation.”

Select one organism and show its cells, affinities, lineage, and colony.

### 1:18–1:43 — Evidence

“Training never receives semantic shape labels. Labels exist only inside a
frozen read-only evaluator. Our checked-in five-seed benchmark used 72 balanced
held-out samples per seed and obtained purity 1.0, mean NMI 0.9699, and mean ARI
0.9641, while every evaluator hash remained unchanged. These are synthetic-shape
results, not a claim of general camera vision.”

Show hidden evaluation, Draw & Audit, and the evidence JSON briefly.

### 1:43–2:14 — GPT-5.6

“GPT-5.6 acts as an external research auditor. Through the OpenAI Responses API
and Structured Outputs, it sees only a frozen aggregate snapshot—never raw
pixels, cell prototypes, tools, or a learning endpoint. It challenges the
evidence, identifies scientific risks, and proposes controlled next experiments.”

Show a completed audit and the state-preserved boundary badges. Avoid recording
the waiting period; use a completed result.

### 2:14–2:38 — Versioned experiments

“The Experiment Studio turns that diagnosis plus optional human instructions
into an allowlisted protocol. It can replicate seeds, vary visual nuisances,
add shapes, or test bounded copies of the learning policy. Every version runs in
a fresh engine. GPT-5.6 cannot edit or delete the submitted baseline and no
generated code is executed.”

Show Baseline v1 locked and one completed version with NMI, ARI, and controls.

### 2:38–2:52 — Codex collaboration and close

“Codex accelerated architecture, implementation, tests, visualization, report
analysis, and VPS deployment throughout Build Week. I made the scientific and
product decisions, including the micro-signature layer, long-lived organisms,
open-ended growth, and immutable baseline. ColonyMind is a transparent first
step toward resource-aware, self-structuring perception.”

End on the 3D architecture and repository/live-demo links.

## Recording checklist

- Record at 1080p with browser zoom adjusted so labels remain legible.
- Use clear English narration; subtitles are recommended.
- Keep the final duration below 3:00 and do not include loading or typing.
- Use no copyrighted music, third-party logos, notifications, API keys, email
  addresses, browser bookmarks, or server terminals.
- Upload early to YouTube as public and test the link while signed
  out.
