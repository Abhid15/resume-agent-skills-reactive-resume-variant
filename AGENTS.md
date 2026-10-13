# Resume repository (Reactive Resume variant)

Fork of [gopinav/resume-agent-skills](https://github.com/gopinav/resume-agent-skills) with optional upload to [Reactive Resume](https://rxresu.me).

## Secrets

Put all API keys in **repo-root `.env`** (gitignored). Copy `.env.example` → `.env`. Never commit `.env`.

## Job tailoring

Use the **`tailor-resume`** skill:

- Read `.cursor/skills/tailor-resume/SKILL.md` (or invoke `/tailor-resume`)
- Treat `resume.md` as the single source of truth for facts
- When the prompt has a **job URL** and little/no pasted JD, scrape first with Firecrawl (`tools/scrape-job` / `.cursor/skills/firecrawl/SKILL.md`) into `jobs/<company-slug>/<role-slug>/jd.md`, then tailor from that file
- If scrape fails, ask the user to paste the JD—do not invent requirements
- Write per-job outputs under `jobs/<company-slug>/<role-slug>/`: `fit-report.md`, `tailored-resume.md`, `cover-letter.md`, and `change-summary.md`
- Cover letters stay **positive** (proof and interest). Gaps belong in `fit-report.md`, not in the letter.
- `tailored-resume.md` must not state negatives, omit content from `resume.md`, or use terse half phrases. Reorder and emphasize only; write full sentences.
- After the first tailored draft, expand cryptic phrasing and run **Humanizer** (`.cursor/skills/humanizer/SKILL.md` plus `references/prose-clarity.md`) on `tailored-resume.md` and `cover-letter.md`. Do not invent facts. Do not Humanize the fit report.
- In `fit-report.md`, include `**Tier:**` and `**Verdict:**` under **Overall fit**.
- When the user asks to **upload to Reactive Resume**, run step 8 of `tailor-resume` (or invoke **`md-to-reactive-resume`**) — never invent JSON by hand.

Do not invent experience. Unsupported requirements belong in the fit report (**Do not add**), not the tailored resume or cover letter. Do not commit `jobs/` (gitignored).
