# md-to-reactive-resume

Convert a **tailored** markdown resume into a Reactive Resume import JSON and optionally upload to [rxresu.me](https://rxresu.me).

## Generative vs deterministic

| Stage | Who | What | Output |
|-------|-----|------|--------|
| **Generative** | `tailor-resume` skill | Tailor `resume.md` to a JD | `jobs/<company>/<role>/tailored-resume.md` (+ fit-report, change-summary) |
| **Deterministic** | This Python script | Parse markdown → fill template → optional API upload | `output/<company>/*.json` + rxresu.me resume |

Do **not** hand-author or LLM-invent the Reactive Resume JSON.

## Upload to Reactive Resume

Requires an API key ([Using the API](https://docs.rxresu.me/guides/using-the-api)):

1. rxresu.me → Settings → API Keys → create key
2. Prefer **repo-root** `.env` (see [`.env.example`](../../.env.example)):

```env
RXRESU_API_KEY=rr_...
```

3. Fallbacks: `tools/md-to-reactive-resume/reactive-resume-api-key.txt` (single line) or `tools/md-to-reactive-resume/.env`

```powershell
python tools/md-to-reactive-resume/scripts/md_to_reactive_resume.py `
  --input jobs/coinbase/em/tailored-resume.md `
  --upload
```

Company/role are inferred from the path under `jobs/`.

## Naming & folders

```
output/
  <company-slug>/
    abhishek-das-<role>-<company-slug>.json
```

Filename pattern: `{name-slug}-{role}-{company-slug}.json`  
Defaults: `abhishek-das` · role from path or `em` · slugified company.

## Options

| Flag | Meaning |
|------|---------|
| `-i` / `--input` | Path to `tailored-resume.md` (**required**) |
| `-c` / `--company` | Optional override; else inferred from path |
| `--role` | Optional role slug; else from path, else `em` |
| `--upload` | Import JSON to rxresu.me (needs `RXRESU_API_KEY`) |
| `--no-upload` | Force local-only |
| `--out-root` | Default: repo `output/` |
| `--api-base` | Default `https://rxresu.me/api/openapi` |
