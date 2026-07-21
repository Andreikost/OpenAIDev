# Third-party notices

ColonyMind is original competition work built on the following direct open
source dependencies. Their respective licenses govern those components.

## Frontend

| Component | License |
| --- | --- |
| React and React DOM | MIT |
| Three.js | MIT |
| Vite and `@vitejs/plugin-react` | MIT |
| TypeScript | Apache-2.0 |
| React and Three.js type definitions | MIT |

## Backend

| Component | License |
| --- | --- |
| FastAPI | MIT |
| Uvicorn | BSD-3-Clause |
| Pydantic | MIT |
| NumPy | BSD-3-Clause and bundled component licenses |
| OpenAI Python SDK | Apache-2.0 |
| HTTPX | BSD-3-Clause |
| PyJWT | MIT |
| SQLAlchemy | MIT |
| Psycopg 3 | LGPL-3.0-only |

Complete dependency versions and transitive packages are recorded in
`frontend/package-lock.json` and the backend container build. License texts are
also included in the installed packages distributed by their publishers.

The interface loads DM Mono and Manrope from Google Fonts; both font families
are distributed under the SIL Open Font License 1.1. Optional authentication
uses the official Google Identity Services client and is subject to Google's
applicable terms. Core judging and anonymous experiments do not require Google
login.

The ColonyMind thumbnail was generated for this project under the entrant's
direction. Earlier source under `D:/GitHub/AI` was used only as a conceptual
research reference; no source code was copied. The detailed reuse declaration
is in `docs/BUILD_WEEK_SCOPE.md`.
