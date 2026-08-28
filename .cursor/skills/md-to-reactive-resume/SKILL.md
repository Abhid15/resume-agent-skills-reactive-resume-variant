---
name: md-to-reactive-resume
description: >-
  Convert tailored-resume.md to Reactive Resume JSON and upload it to rxresu.me
  via the API. Infers company from the markdown path. Use when the user invokes
  md-to-reactive-resume, asks to convert/upload a tailored resume to Reactive
  Resume, or needs abhishek-das-em-<company>.json on rxresu.me.
disable-model-invocation: true
---

# md-to-reactive-resume

Deterministic MD → Reactive Resume JSON → **upload to rxresu.me**.  
Do **not** hand-write JSON or invent resume facts.

## Prerequisites (once)

1. Create an API key at [rxresu.me](https://rxresu.me) → Settings → API Keys  
   ([docs](https://docs.rxresu.me/guides/using-the-api))
2. Store it (pick one; never commit):
   - `tools/md-to-reactive-resume/reactive-resume-api-key.txt` (single-line key), or
   - `tools/md-to-reactive-resume/.env` with `RXRESU_API_KEY=...`, or
   - env var `RXRESU_API_KEY`

Never print or commit the API key.

## Invoke

User points at a tailored markdown and asks for this skill / convert+upload.

## Steps

1. Resolve the input `.md` path (usually `jobs/<company>/<role>/tailored-resume.md`).
2. Run the converter **with `--upload`** (company/role inferred from path).
3. Reply with: local JSON path, resume id, name/slug, and dashboard link.

## Command

From the repo root:

```powershell
python tools/md-to-reactive-resume/scripts/md_to_reactive_resume.py `
  --input <path-to-tailored-resume.md> `
  --upload
```

Use `--no-upload` only if the user explicitly wants a local JSON file and no API call.

## Path → company (and role)

| Markdown location | Company | Role slug |
|-------------------|---------|-----------|
| `jobs/coinbase/em/tailored-resume.md` | `coinbase` | `em` |
| `jobs/coupa-software/tailored-resume.md` | `coupa-software` | `em` (default) |
| `jobs/coinbase/engineering-manager/tailored-resume.md` | `coinbase` | `engineering-manager` |

## Outputs

**Local**
```
output/<company-slug>/abhishek-das-<role>-<company-slug>.json
```

**Remote (upload)**  
`POST /api/openapi/resumes/import` then `PUT /resumes/{id}` to set:

- `name` / `slug`: `abhishek-das-<role>-<company-slug>`
- `tags`: `[company-slug, role]`

Open: https://rxresu.me/dashboard/resumes

## Do not

- Re-implement conversion or upload in chat
- Skip `--upload` unless the user asks for local-only
- Paste API keys into chat or commit `.env`
