# Security

## Reporting issues

If you discover a security vulnerability, please report it privately to the repository maintainer rather than opening a public issue.

## Secrets

Never commit:

- `.env` or files containing API keys
- Real customer call recordings or transcripts
- Production `outputs/` from real businesses

`.gitignore` excludes `.env` and `outputs/` by default. Before pushing to a public remote, run:

```bash
git status
git grep -i "sk-proj" || echo "No OpenAI key patterns found"
```

If an API key was ever committed, **rotate it immediately** and remove it from git history.

## Local data

Milestone 1 stores files on disk under `data/` and `outputs/`. Restrict filesystem permissions on machines that hold real pilot data.
