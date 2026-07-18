# Repository and deployment workflow

## Source of truth

- Local repository: `D:/GitHub/OpenAIDev`
- GitHub remote: `https://github.com/Andreikost/OpenAIDev.git`
- Public target: `https://openaidev.automationfreelancer.com`

GitHub is the source of truth for VPS updates. Production must run a known,
tested commit or release tag.

## Local Git

If `git` is not on `PATH`, use the copy bundled with GitHub Desktop. The current
known location is:

```text
C:/Users/Andres/AppData/Local/GitHubDesktop/app-3.6.3/resources/app/git/cmd/git.exe
```

Work in focused branches, stage explicit paths, run relevant tests, and commit
coherent milestones. Keep generated dependencies, private reports, credentials,
and local environment files out of Git.

## Secrets

Existing VPS credentials under `D:/GitHub/AI` are local read-only references.
Never print, copy, summarize, commit, or upload their values. OpenAIDev contains
only `.env.example` placeholders. Actual values belong in a local environment
or a server-only environment file outside the repository.

## VPS release pattern

1. Verify the exact host, SSH identity, reverse proxy, Docker network, and app
   path without exposing credentials.
2. Back up an existing OpenAIDev deployment if present.
3. Pull a tested GitHub commit or release into the verified application path.
4. Load server-only environment variables.
5. Build and start only the OpenAIDev Docker Compose services.
6. Verify health, TLS, routing, streaming, report export, and the judge journey.
7. Record the deployed commit SHA and non-secret health result.
8. Roll back to the previous tested commit if validation fails.

Do not replace unrelated applications or deploy local uncommitted archives as
the primary release workflow.
