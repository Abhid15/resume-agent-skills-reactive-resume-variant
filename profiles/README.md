# Profiles

Each person is a folder here. The tailor and upload skills share one repo; facts, job folders, and Reactive Resume keys stay inside one profile.

## Add a person

1. Pick a slug: lowercase, hyphenated (`jane-doe`).
2. Create `profiles/<slug>/resume.md`. This file is gitignored. It is the only source of truth for that person's facts.
3. In the repo-root `.env`, set `RXRESU_API_KEY_<SLUG>` to that person's rxresu.me API key. The suffix is the slug in uppercase with hyphens turned into underscores (`jane-doe` → `RXRESU_API_KEY_JANE_DOE`).
4. Run `/tailor-resume` with `Profile: <slug>` plus the company, role, and job URL.

Outputs land in `jobs/<slug>/<company>/<role>/`. Uploads land in `output/<slug>/<company>/` and on that person's rxresu.me account.

If the prompt omits `Profile:` and exactly one `profiles/*/resume.md` exists, that profile is used. If several exist, the run stops and asks which one.

For the `abhishek` profile only, an unset `RXRESU_API_KEY_ABHISHEK` falls back to `RXRESU_API_KEY`. Every other profile must have its own key. A missing key stops the upload.
