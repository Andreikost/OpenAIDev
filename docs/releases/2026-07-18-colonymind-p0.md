# ColonyMind P0 — first VPS release

- Public URL: `https://openaidev.automationfreelancer.com`
- Application commit: `04702e49e2444d4cd58648304b388ad146f47c69`
- Release archive SHA-256:
  `4060ce914267a190a5f68b63bd773047b3014e4a2bb18dfb77a6b7bf835ab3ce`
- Deployment target: `/opt/openaidev`
- Services: isolated Docker Compose backend and frontend; frontend is bound to
  loopback port `8200` and routed by the dedicated Nginx virtual host.

## Checks performed

1. Python test suite: `6 passed`.
2. React type check and production build: passed.
3. Local API journey: starts with zero organisms; a deterministic run forms
   three organisms and one colony; hidden evaluation and ablation do not mutate
   state.
4. Public HTTPS journey: health endpoint passed; starts at zero organisms;
   after 240 public API steps, three organisms and one colony exist; hidden
   evaluation reports `modelModified: false`.
5. TLS certificate was issued for the public subdomain and automatic renewal is
   configured by Certbot.

## Follow-up

The VPS currently lacks a read-only GitHub deploy key, so this initial release
used a checksum-verified archive generated from `origin/main`. Configure a
repository-scoped read-only deploy key before using the automated pull-based
release script for future versions.
