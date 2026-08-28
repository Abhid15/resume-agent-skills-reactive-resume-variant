# Resume Agent — Reactive Resume variant

Fork of [gopinav/resume-agent-skills](https://github.com/gopinav/resume-agent-skills) (`resume-agent-skills-reactive-resume-variant`).

Adds deterministic **markdown → Reactive Resume JSON → rxresu.me upload** after (or instead of) re-tailoring, so one Cursor window covers tailor → upload.

Upstream remote: `upstream` → `gopinav/resume-agent-skills`  
Your remote: `origin` → your fork

## Setup

1. Clone **your** fork (or use this repo after remotes are wired).
2. In Cursor, open this folder (and connect the GitHub repo for cloud agents if needed).
3. Keep `resume.md` on `main` as your canonical profile.
4. Optional — Reactive Resume upload:
   - Create an API key at [rxresu.me → Settings → API Keys](https://docs.rxresu.me/guides/using-the-api)
   - Save it as `tools/md-to-reactive-resume/reactive-resume-api-key.txt` (gitignored) or `RXRESU_API_KEY` in env / `.env`

## First run (tailor)

Use the Resume Agent Chrome extension / API, or invoke **`tailor-resume`** in Cursor with a job description. The agent should:

1. Read `resume.md`
2. Follow `.cursor/skills/tailor-resume/SKILL.md`
3. Write under `jobs/<company>/<role>/`:
   - `fit-report.md`
   - `tailored-resume.md`
   - `change-summary.md`
4. Open a PR via `autoCreatePR` (cloud agent flows)

`fit-report.md` must include **Overall fit** with `**Tier:**`, `**Verdict:**`, Strong matches, Gaps, and **Do not add**.

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

Details: [`tools/md-to-reactive-resume/README.md`](tools/md-to-reactive-resume/README.md)

## Skills

| Skill | Purpose |
|-------|---------|
| `tailor-resume` | Fit report + tailored MD + change summary (+ optional upload step) |
| `md-to-reactive-resume` | Convert/upload only (no re-tailor) |
