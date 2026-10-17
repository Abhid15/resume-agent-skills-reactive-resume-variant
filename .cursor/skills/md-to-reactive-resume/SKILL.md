---
name: md-to-reactive-resume
description: >-
  Convert tailored-resume.md to Reactive Resume JSON and upload it to that
  profile's rxresu.me account via the API. Infers profile and company from the
  markdown path. Use when the user invokes md-to-reactive-resume, asks to
  convert/upload a tailored resume to Reactive Resume, or needs
  <name>-<role>-<company>.json on rxresu.me.
disable-model-invocation: true
---

# md-to-reactive-resume

Deterministic MD → Reactive Resume JSON → **upload to rxresu.me**.  
Do **not** hand-write JSON or invent resume facts.

## Prerequisites (once per profile)

1. Create an API key at [rxresu.me](https://rxresu.me) → Settings → API Keys  
   ([docs](https://docs.rxresu.me/guides/using-the-api))
2. Store it in repo-root `.env` as `RXRESU_API_KEY_<SLUG>` (never commit):
   - Profile `jane-doe` → `RXRESU_API_KEY_JANE_DOE`
   - Profile `abhishek` may fall back to `RXRESU_API_KEY` when `RXRESU_API_KEY_ABHISHEK` is unset
3. Other profiles do not fall back to another person's key or to the tool-local key file.

Never print or commit the API key.

## Invoke

User points at a tailored markdown and asks for this skill / convert+upload.

## Steps

1. Resolve the input `.md` path (usually `jobs/<profile>/<company>/<role>/tailored-resume.md`).
2. Run the converter **with `--upload`** (profile/company/role inferred from path).
3. Reply with: local JSON path, profile, resume id, name/slug, and dashboard link.

## Command

From the repo root:

```powershell
python tools/md-to-reactive-resume/scripts/md_to_reactive_resume.py `
  --input <path-to-tailored-resume.md> `
  --upload
```

Use `--no-upload` only if the user explicitly wants a local JSON file and no API call.

## Path → profile, company, and role

| Markdown location | Profile | Company | Role slug |
|-------------------|---------|---------|-----------|
| `jobs/abhishek/coinbase/em/tailored-resume.md` | `abhishek` | `coinbase` | `em` |
| `jobs/jane-doe/coinbase/engineering-manager/tailored-resume.md` | `jane-doe` | `coinbase` | `engineering-manager` |
| `jobs/coinbase/em/tailored-resume.md` | (none; legacy) | `coinbase` | `em` |

The first folder under `jobs/` is a profile when `profiles/<that-folder>/` exists. Otherwise it is the company (older layout).

The filename prefix is the slug of the markdown `# Name` line, unless `--name-slug` is passed.

## Outputs

**Local**
```
output/<profile>/<company-slug>/<name-slug>-<role>-<company-slug>.json
```

**Remote (upload)**  
`POST /api/openapi/resumes/import` then `PUT /resumes/{id}` to set:

- `name` / `slug`: `<name-slug>-<role>-<company-slug>`
- `tags`: `[company-slug, role]`

The request uses that profile's API key, so the resume lands on their rxresu.me account.

Open: https://rxresu.me/dashboard/resumes

## Do not

- Re-implement conversion or upload in chat
- Skip `--upload` unless the user asks for local-only
- Paste API keys into chat or commit `.env`
- Upload one profile's resume with another profile's key
