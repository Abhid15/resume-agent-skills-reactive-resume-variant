---
name: tailor-resume
description: Tailor one profile's resume.md for a specific job—fit report, honest tailored resume, cover letter, change summary. Humanize resume and cover-letter prose. Optionally convert and upload tailored-resume.md to that person's Reactive Resume (rxresu.me) account when the user asks.
---

# Tailor resume for one job

## Source of truth

Each person is a profile slug (`profiles/<slug>/resume.md`, gitignored). See `profiles/README.md`.

- Resolve the profile before reading or writing:
  - Use `Profile: <slug>` from the prompt when it is present.
  - If it is omitted and exactly one `profiles/*/resume.md` exists, use that profile.
  - If it is omitted and more than one profile resume exists, stop and ask which profile. Do not scrape or write yet.
- Read `profiles/<slug>/resume.md` before editing anything. If that file is missing, stop and ask for it.
- In the references below, `resume.md` means that profile file.
- JD requirements not supported by that file go in fit report **Do not add** only—never into `tailored-resume.md` or `cover-letter.md`.

The actual resume output must not:

- state negatives ( I don't do this I don't do that)
- omit stuff from base resume, only position relevant stuff better
- write in terse trite half phrases, write in full sentneces

Apply that as: keep every role, bullet fact, skill, certification, award, language, and education line from `profiles/<slug>/resume.md`. Reorder and rephrase so JD-relevant items come first and read as complete sentences. Do not announce what the candidate does not do. Gaps stay in `fit-report.md` only.

## Workflow

1. **Ingest** — Read the per-run prompt (company, role, URL, JD, output paths).
   - If a job **URL** is present and there is **no substantial pasted JD**, scrape first (do not invent JD text):
     ```powershell
     python tools/scrape-job/scripts/scrape_job.py `
       --url "<job-url>" `
       --profile <profile-slug> `
       --company <company-slug> `
       --role <role-slug>
     ```
     Prefer Firecrawl CLI when installed (`firecrawl scrape`); the script uses CLI if available, else Firecrawl Cloud API. Requires `FIRECRAWL_API_KEY` in repo-root `.env` (see `.env.example`). Live Firecrawl usage details: `.cursor/skills/firecrawl/SKILL.md`.
   - Read `jobs/<profile-slug>/<company-slug>/<role-slug>/jd.md` as the JD source when scraped.
   - If scrape fails or returns empty/login-wall content, **stop and ask the user to paste the JD**—do not invent requirements.
   - Load `references/jd-extraction-taxonomy.md` and classify JD requirements.
2. **Fit report** — Load `references/fit-report.md`. Pick the fit tier from that reference and include the required `**Verdict:**` line. Write `jobs/<profile-slug>/<company-slug>/<role-slug>/fit-report.md` with **Overall fit**, **Strong matches**, **Gaps**, **Do not add**. Do not Humanize the fit report.
3. **Tailor** — Load `references/keyword-alignment.md` and `references/markdown-resume-structure.md`. Write `tailored-resume.md` from `profiles/<slug>/resume.md` only: reorder and emphasize; do not drop base content, do not state negatives, write full sentences.
4. **Cover letter** — Load `references/cover-letter.md`. Write a **positive** `cover-letter.md` (proof and interest; gaps stay in the fit report).
5. **Clarity + Humanizer** — Load `references/prose-clarity.md` and `.cursor/skills/humanizer/SKILL.md`. Expand cryptic phrasing, then Humanize `tailored-resume.md` and `cover-letter.md` in embedded/file mode (final text only). Keep facts, metrics, and JD-aligned keywords.
6. **Change summary** — Load `references/change-summary.md`. Document every meaningful edit in `change-summary.md`.
7. **Quality** — Skim `references/anti-patterns.md` and `references/agent-governance.md`. Optional: note plaintext test steps from `references/export-and-plaintext-test.md`.
8. **Reactive Resume upload (optional)** — Run **only** when the user asks to upload (e.g. “and upload to reactive resume”, “md-to-reactive-resume”, or `--upload`). Do not invent JSON; run the deterministic script:

```powershell
python tools/md-to-reactive-resume/scripts/md_to_reactive_resume.py `
  --input jobs/<profile-slug>/<company-slug>/<role-slug>/tailored-resume.md `
  --upload
```

- Profile, company, and role are inferred from that path. Upload uses `RXRESU_API_KEY_<SLUG>` from repo-root `.env` (for `abhishek` only, `RXRESU_API_KEY` is the fallback). Do not upload with another profile's key.
- Reply with local JSON path (`output/...`), resume id/name/slug, and https://rxresu.me/dashboard/resumes
- If the API key is missing, keep the markdown outputs and report the key setup error clearly (see `tools/md-to-reactive-resume/README.md`).
- For upload-only (no re-tailor), invoke the **`md-to-reactive-resume`** skill instead.

## Output paths

Per-run prompt specifies:

- `jobs/<profile-slug>/<company-slug>/<role-slug>/jd.md` (when scraped from URL)
- `jobs/<profile-slug>/<company-slug>/<role-slug>/fit-report.md`
- `jobs/<profile-slug>/<company-slug>/<role-slug>/tailored-resume.md`
- `jobs/<profile-slug>/<company-slug>/<role-slug>/cover-letter.md`
- `jobs/<profile-slug>/<company-slug>/<role-slug>/change-summary.md`

Slug rules: lowercase, hyphenated; strip legal suffixes (Inc, LLC, Ltd) from company names.

## Secrets

All PATs live in **repo-root `.env`** (gitignored). Copy `.env.example` → `.env`. Never commit `.env` or print keys in chat.

## PR

Title: `feat: tailor resume for <role> at <company>`

Commit skill/tooling changes on the agent branch. Do **not** commit `jobs/` outputs, `.env`, or any `resume.md` (including `profiles/<slug>/resume.md`).
