# Resume Agent — Reactive Resume variant

Fork of [gopinav/resume-agent-skills](https://github.com/gopinav/resume-agent-skills) (`resume-agent-skills-reactive-resume-variant`).

Adds:

- **Firecrawl Cloud** scrape for job URLs → `jobs/<company>/<role>/jd.md`
- Deterministic **markdown → Reactive Resume JSON → rxresu.me upload**

So one Cursor window covers scrape → tailor → upload.

Upstream remote: `upstream` → `gopinav/resume-agent-skills`  
Your remote: `origin` → your fork

## Setup

1. Clone **your** fork (or use this repo after remotes are wired).
2. In Cursor, open this folder (and connect the GitHub repo for cloud agents if needed).
3. Keep `resume.md` on `main` as your canonical profile.
4. **Secrets (all PATs in one place):**
   - Copy [`.env.example`](.env.example) → `.env` (gitignored — never commit)
   - Set `FIRECRAWL_API_KEY` from [firecrawl.dev](https://www.firecrawl.dev)
   - Set `RXRESU_API_KEY` from [rxresu.me → Settings → API Keys](https://docs.rxresu.me/guides/using-the-api)
   - Optional fallbacks still work: `tools/md-to-reactive-resume/reactive-resume-api-key.txt`
5. Optional — install Firecrawl CLI for live scrape (see `.cursor/skills/firecrawl/SKILL.md`):
   ```bash
   npx -y firecrawl-cli@latest init --all --browser
   ```
   The Python scrape helper works with the Cloud API alone if the CLI is not installed.

## First run (tailor)

Typical prompt (URL-only is fine):

```text
/tailor-resume

Company: Acme
Role: Engineering Manager
URL: https://...
Also upload to Reactive Resume.
```

The agent should:

1. Read `resume.md`
2. Follow `.cursor/skills/tailor-resume/SKILL.md`
3. If URL present and JD not pasted → scrape to `jobs/<company>/<role>/jd.md` via Firecrawl
4. Write under `jobs/<company>/<role>/`:
   - `fit-report.md`
   - `tailored-resume.md`
   - `change-summary.md`
5. Optionally upload to Reactive Resume when asked
6. Open a PR via `autoCreatePR` (cloud agent flows) — **do not commit `jobs/` or `.env`**

`fit-report.md` must include **Overall fit** with `**Tier:**`, `**Verdict:**`, Strong matches, Gaps, and **Do not add**.

Manual scrape:

```powershell
python tools/scrape-job/scripts/scrape_job.py `
  --url "https://..." `
  --company acme `
  --role engineering-manager
```

## Upload to Reactive Resume (optional)

When you want the tailored resume on [rxresu.me](https://rxresu.me):

- Ask **`tailor-resume`** to also upload, **or**
- Invoke **`md-to-reactive-resume`** on an existing `tailored-resume.md`

```powershell
python tools/md-to-reactive-resume/scripts/md_to_reactive_resume.py `
  --input jobs/<company>/<role>/tailored-resume.md `
  --upload
```

Outputs land in `output/<company>/` locally and on https://rxresu.me/dashboard/resumes.

Details: [`tools/md-to-reactive-resume/README.md`](tools/md-to-reactive-resume/README.md) · [`tools/scrape-job/README.md`](tools/scrape-job/README.md)

## Skills

| Skill | Purpose |
|-------|---------|
| `tailor-resume` | Scrape (if needed) + fit report + tailored MD + change summary (+ optional upload) |
| `md-to-reactive-resume` | Convert/upload only (no re-tailor) |
| `firecrawl` | Live Firecrawl CLI / Cloud usage for web scrape and related tools |

## Notes

- `jobs/` and `output/` (except `.gitkeep`) are gitignored — tailored JDs stay local.
- LinkedIn and some ATS pages may still block scrapes; paste the JD if `jd.md` is empty.
