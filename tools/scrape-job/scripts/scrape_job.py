#!/usr/bin/env python3
"""Scrape a job posting URL to markdown via Firecrawl Cloud (fallback if CLI missing)."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[3]
FIRECRAWL_SCRAPE = "https://api.firecrawl.dev/v1/scrape"


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = val


def resolve_firecrawl_key() -> str:
    load_env_file(REPO_ROOT / ".env")
    load_env_file(REPO_ROOT / "tools" / "scrape-job" / ".env")
    key = (os.environ.get("FIRECRAWL_API_KEY") or "").strip()
    if not key:
        for candidate in (
            REPO_ROOT / "tools" / "scrape-job" / "firecrawl-api-key.txt",
        ):
            if candidate.is_file():
                key = candidate.read_text(encoding="utf-8").strip().splitlines()[0].strip()
                if key:
                    break
    if not key:
        raise SystemExit(
            "Missing FIRECRAWL_API_KEY. Set it in repo-root .env "
            "(copy from .env.example). Get a key at https://www.firecrawl.dev"
        )
    return key


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "unknown"


def infer_company_role(url: str, company: str | None, role: str | None) -> tuple[str, str]:
    if company and role:
        return slugify(company), slugify(role)

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    parts = [p for p in parsed.path.split("/") if p]

    if not company:
        # jobs.ashbyhq.com/org/... → org; linkedin.com → linkedin; stripe.com → stripe
        if "ashbyhq.com" in host and parts:
            company = parts[0]
        elif host.endswith("linkedin.com"):
            company = "linkedin"
        else:
            company = host.split(".")[0] if host else "unknown"

    if not role:
        # Prefer last meaningful path segment
        role = parts[-1] if parts else "role"
        role = re.sub(r"^\d+-", "", role)  # strip numeric ids prefix
        if len(role) < 3 and len(parts) >= 2:
            role = parts[-2]

    return slugify(company), slugify(role)


def write_jd(path: Path, url: str, markdown: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = markdown.strip()
    if not body:
        raise SystemExit("Scrape returned empty markdown. Paste the JD manually.")
    content = (
        f"---\n"
        f"source_url: {url}\n"
        f"scraped_at: {scraped_at}\n"
        f"---\n\n"
        f"{body}\n"
    )
    path.write_text(content, encoding="utf-8")


def scrape_via_cli(url: str, out: Path) -> bool:
    exe = shutil.which("firecrawl")
    if not exe:
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    # Ensure key from .env is visible to CLI
    resolve_firecrawl_key()
    env = os.environ.copy()
    try:
        subprocess.run(
            [exe, "scrape", url, "-o", str(out)],
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or str(e)).strip()
        raise SystemExit(f"firecrawl CLI failed: {err}") from e
    # CLI may write raw markdown without front matter — wrap if needed
    raw = out.read_text(encoding="utf-8") if out.is_file() else ""
    if not raw.strip():
        raise SystemExit("firecrawl CLI wrote an empty file. Paste the JD manually.")
    if not raw.lstrip().startswith("---"):
        write_jd(out, url, raw)
    return True


def scrape_via_api(url: str, out: Path) -> None:
    key = resolve_firecrawl_key()
    payload = json.dumps(
        {
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        FIRECRAWL_SCRAPE,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Firecrawl HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"Firecrawl request failed: {e}") from e

    md = ""
    if isinstance(data, dict):
        inner = data.get("data") if isinstance(data.get("data"), dict) else data
        if isinstance(inner, dict):
            md = inner.get("markdown") or inner.get("content") or ""
    if not (md or "").strip():
        raise SystemExit(
            "Firecrawl returned no markdown (login wall or blocked page). "
            "Paste the JD into the prompt and retry."
        )
    write_jd(out, url, md)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", "-u", required=True, help="Job posting URL")
    parser.add_argument("--company", "-c", help="Company slug or name")
    parser.add_argument("--role", "-r", help="Role slug or title")
    parser.add_argument(
        "--profile",
        "-p",
        help="Profile slug (default output: jobs/<profile>/<company>/<role>/jd.md)",
    )
    parser.add_argument(
        "--out",
        "-o",
        help="Output path (default: jobs/<profile>/<company>/<role>/jd.md when --profile is set)",
    )
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="Skip firecrawl CLI; use HTTP API only",
    )
    args = parser.parse_args()

    company, role = infer_company_role(args.url, args.company, args.role)
    profile = slugify(args.profile) if args.profile else ""
    if args.out:
        out = Path(args.out)
    elif profile:
        out = REPO_ROOT / "jobs" / profile / company / role / "jd.md"
    else:
        out = REPO_ROOT / "jobs" / company / role / "jd.md"
    if not out.is_absolute():
        out = REPO_ROOT / out

    if not args.api_only and scrape_via_cli(args.url, out):
        print(f"jd: {out}")
        if profile:
            print(f"profile_slug: {profile}")
        print(f"company_slug: {company}")
        print(f"role_slug: {role}")
        print("method: firecrawl-cli")
        return

    scrape_via_api(args.url, out)
    print(f"jd: {out}")
    if profile:
        print(f"profile_slug: {profile}")
    print(f"company_slug: {company}")
    print(f"role_slug: {role}")
    print("method: firecrawl-api")


if __name__ == "__main__":
    main()
