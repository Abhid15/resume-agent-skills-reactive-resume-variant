# scrape-job

Scrape a job posting URL to `jobs/<company>/<role>/jd.md` using **Firecrawl Cloud**.

Prefer the [Firecrawl skill](../../.cursor/skills/firecrawl/SKILL.md) / CLI when available. This script is the **fallback** (and a convenient path helper) used by `tailor-resume` ingest.

## Setup

1. Copy [`.env.example`](../../.env.example) → repo-root `.env`
2. Set `FIRECRAWL_API_KEY=fc-...` (from [firecrawl.dev](https://www.firecrawl.dev))
3. Never commit `.env`

## Usage

From repo root:

```powershell
python tools/scrape-job/scripts/scrape_job.py `
  --url "https://example.com/jobs/123" `
  --company acme `
  --role software-engineering-manager
```

Optional: `--api-only` to skip the `firecrawl` CLI and call the HTTP API directly.

## Output

```text
jobs/<company-slug>/<role-slug>/jd.md
```

Front matter includes `source_url` and `scraped_at`.

## Limits

LinkedIn and some ATS pages may return login shells or empty content. If that happens, paste the JD into the tailor prompt instead.
