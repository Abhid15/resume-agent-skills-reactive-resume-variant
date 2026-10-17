# md-to-reactive-resume

Convert a **tailored** markdown resume into a Reactive Resume import JSON and optionally upload to [rxresu.me](https://rxresu.me).

## Generative vs deterministic

| Stage | Who | What | Output |
|-------|-----|------|--------|
| **Generative** | `tailor-resume` skill | Tailor `profiles/<slug>/resume.md` to a JD | `jobs/<profile>/<company>/<role>/tailored-resume.md` (+ fit-report, change-summary) |
| **Deterministic** | This Python script | Parse markdown → fill template → optional API upload | `output/<profile>/<company>/*.json` + that person's rxresu.me resume |

Do **not** hand-author or LLM-invent the Reactive Resume JSON.

## Upload to Reactive Resume

Requires an API key ([Using the API](https://docs.rxresu.me/guides/using-the-api)):

1. rxresu.me → Settings → API Keys → create key
2. Prefer **repo-root** `.env` (see [`.env.example`](../../.env.example)). One key per profile:

```env
RXRESU_API_KEY_ABHISHEK=rr_...
RXRESU_API_KEY_JANE_DOE=rr_...
```

The suffix is the profile slug in uppercase with hyphens turned into underscores. For `abhishek` only, an unset `RXRESU_API_KEY_ABHISHEK` falls back to `RXRESU_API_KEY`.

3. Fallbacks for the abhishek key only: `tools/md-to-reactive-resume/reactive-resume-api-key.txt` (single line) or `tools/md-to-reactive-resume/.env`

```powershell
python tools/md-to-reactive-resume/scripts/md_to_reactive_resume.py `
  --input jobs/abhishek/coinbase/em/tailored-resume.md `
  --upload
```

Profile, company, and role are inferred from the path under `jobs/`. The first folder is a profile when `profiles/<folder>/` exists.

## Naming & folders

```
output/
  <profile>/
    <company-slug>/
      <name-slug>-<role>-<company-slug>.json
```

Filename pattern: `{name-slug}-{role}-{company-slug}.json`  
`name-slug` comes from the markdown `# Name` line. Role comes from the path, or `em`. Company is slugified.

## Options

| Flag | Meaning |
|------|---------|
| `-i` / `--input` | Path to `tailored-resume.md` (**required**) |
| `--profile` | Profile slug. Selects `RXRESU_API_KEY_<SLUG>` and `output/<profile>/` |
| `-c` / `--company` | Optional override; else inferred from path |
| `--role` | Optional role slug; else from path, else `em` |
| `--name-slug` | Optional filename prefix; else the `# Name` line |
| `--upload` | Import JSON to that profile's rxresu.me account |
| `--no-upload` | Force local-only |
| `--out-root` | Default: repo `output/` |
| `--api-base` | Default `https://rxresu.me/api/openapi` |
