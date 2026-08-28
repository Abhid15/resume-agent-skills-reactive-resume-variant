#!/usr/bin/env python3
"""
Deterministic converter: tailored-resume.md → Reactive Resume JSON.

No LLM. Parse markdown → fill template → write
  <out-root>/<company-slug>/abhishek-das-em-<company-slug>.json

Expected markdown shape (resume-agent / tailor-resume format):

  # Name
  contact line
  ## Summary
  ## Work Experience
  ### Title — Company (dates)
  - bullets
  ## Skills
  - **Group:** a, b, c
  ## Certifications   (optional)
  ## Awards & recognition  (optional)
  ## Education
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any


LEGAL_SUFFIXES = re.compile(
    r"\b(inc|incorporated|llc|ltd|limited|corp|corporation|co|company|plc|gmbh|ag|sa|nv)\b\.?",
    re.I,
)


def slugify_company(name: str) -> str:
    s = name.strip()
    s = LEGAL_SUFFIXES.sub("", s)
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        raise ValueError(f"Could not derive company slug from: {name!r}")
    return s


def esc_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def new_id() -> str:
    return str(uuid.uuid4())


def section_body(md: str, heading: str, next_headings: list[str]) -> str | None:
    """Return body under ## heading until next known ## or EOF."""
    start = re.search(rf"^## {re.escape(heading)}\s*$", md, re.M)
    if not start:
        return None
    rest = md[start.end() :]
    end = len(rest)
    for h in next_headings:
        m = re.search(rf"^## {re.escape(h)}\s*$", rest, re.M)
        if m:
            end = min(end, m.start())
    return rest[:end].strip()


def parse_summary(md: str) -> str:
    body = section_body(
        md,
        "Summary",
        ["Work Experience", "Skills", "Certifications", "Awards & recognition", "Education"],
    )
    if not body:
        raise ValueError("Missing ## Summary")
    return re.sub(r"\n+", " ", body).strip()


def parse_jobs(md: str) -> list[dict[str, Any]]:
    body = section_body(
        md,
        "Work Experience",
        ["Skills", "Certifications", "Awards & recognition", "Education"],
    )
    if not body:
        raise ValueError("Missing ## Work Experience")

    blocks = re.split(r"^### ", body, flags=re.M)
    jobs: list[dict[str, Any]] = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        header, _, rest = block.partition("\n")
        header = header.strip()
        m = re.match(r"(.+?) — (.+?) \((.+?)\)\s*$", header)
        if not m:
            raise ValueError(
                f"Job header must be '### Title — Company (dates)', got: {header!r}"
            )
        position, company, period = (
            m.group(1).strip(),
            m.group(2).strip(),
            m.group(3).strip().replace("–", " - ").replace("—", " - "),
        )
        bullets = re.findall(r"^- (.+)$", rest, flags=re.M)
        notable_m = re.search(r"\*\*Notable work:\*\*\s*(.+)$", rest, flags=re.M)
        html_parts = ["<ul>"]
        for b in bullets:
            html_parts.append(f"<li>{format_bullet_html(b)}</li>")
        html_parts.append("</ul>")
        if notable_m:
            html_parts.append(
                f"<p><strong>Notable work:</strong> {esc_html(notable_m.group(1).strip())}</p>"
            )
        location = "Pune, IN" if "coupa" in company.lower() else ""
        jobs.append(
            {
                "position": position,
                "company": company,
                "period": period,
                "location": location,
                "description": "".join(html_parts),
            }
        )
    if not jobs:
        raise ValueError("No experience entries found under ## Work Experience")
    return jobs


def format_bullet_html(text: str) -> str:
    """Bold a short Label: prefix when present; otherwise escape whole line."""
    if ": " in text:
        head, rest = text.split(": ", 1)
        if 0 < len(head) < 70 and not head.startswith("http"):
            return f"<strong>{esc_html(head)}:</strong> {esc_html(rest)}"
    return esc_html(text)


def parse_skills(md: str) -> list[dict[str, Any]]:
    body = section_body(
        md,
        "Skills",
        ["Certifications", "Awards & recognition", "Education"],
    )
    if not body:
        raise ValueError("Missing ## Skills")
    items: list[dict[str, Any]] = []
    for line in body.splitlines():
        m = re.match(r"^- \*\*(.+?):\*\*\s*(.+)$", line.strip())
        if not m:
            continue
        keywords = [k.strip() for k in m.group(2).split(",") if k.strip()]
        items.append({"name": m.group(1).strip(), "keywords": keywords})
    if not items:
        raise ValueError("No skill groups found (expected '- **Group:** a, b')")
    return items


def parse_certifications(md: str) -> list[dict[str, str]]:
    body = section_body(
        md, "Certifications", ["Awards & recognition", "Education"]
    )
    if not body:
        return []
    certs: list[dict[str, str]] = []
    for line in body.splitlines():
        m = re.match(r"^- (.+?)\s*\((\d{4})\)\s*$", line.strip())
        if m:
            title = m.group(1).strip()
            issuer = ""
            if "AWS" in title:
                issuer = "Amazon Web Services"
            elif "Scrum" in title:
                issuer = "Scrum Alliance"
            certs.append({"title": title, "date": m.group(2), "issuer": issuer})
    return certs


def parse_awards(md: str) -> list[dict[str, str]]:
    body = section_body(md, "Awards & recognition", ["Education"])
    if not body:
        return []
    awards: list[dict[str, str]] = []
    for line in body.splitlines():
        if not line.strip().startswith("- "):
            continue
        text = line.strip()[2:].strip()
        title = text
        awarder = ""
        date = ""
        description = ""
        if " — " in text:
            title, rest = text.split(" — ", 1)
            title = title.strip()
            if " (" in rest and rest.rstrip().endswith(")"):
                awarder = rest.split(" (")[0].strip()
                description = rest[rest.find("(") + 1 : rest.rfind(")")].strip()
            else:
                awarder = rest.strip()
        ym = re.search(r"\((\d{4})\)", title)
        if ym:
            date = ym.group(1)
            title = re.sub(r"\s*\(\d{4}\)", "", title).strip()
        if not date:
            ym2 = re.search(r"\b(20\d{2}|19\d{2})\b", text)
            if ym2:
                date = ym2.group(1)
        awards.append(
            {
                "title": title,
                "awarder": awarder,
                "date": date,
                "description": f"<p>{esc_html(description)}</p>" if description else "",
            }
        )
    return awards


def parse_education(md: str) -> dict[str, str]:
    body = section_body(md, "Education", [])
    if not body:
        raise ValueError("Missing ## Education")
    line = body.strip().splitlines()[0].strip()
    # Degree — School (years), CGPA x
    m = re.match(
        r"(.+?)\s*—\s*(.+?)\s*\((.+?)\)(?:,\s*CGPA\s*(.+))?$",
        line,
    )
    if not m:
        raise ValueError(
            f"Education line must be 'Degree — School (years), CGPA x', got: {line!r}"
        )
    degree = m.group(1).strip()
    school = m.group(2).strip()
    period = m.group(3).strip().replace("–", " - ")
    grade = f"CGPA {m.group(4).strip()}" if m.group(4) else ""
    area = ""
    if "Electrical" in degree:
        area = "Electrical Engineering"
    return {
        "degree": degree,
        "school": school,
        "period": period,
        "grade": grade,
        "area": area,
    }


def parse_basics(md: str) -> dict[str, str]:
    lines = [ln.strip() for ln in md.strip().splitlines() if ln.strip()]
    if not lines or not lines[0].startswith("# "):
        raise ValueError("Resume must start with '# Name'")
    name = lines[0][2:].strip()
    contact = lines[1] if len(lines) > 1 else ""
    parts = [p.strip() for p in contact.split("·")]
    location = parts[0] if parts else ""
    email = next((p for p in parts if "@" in p), "")
    phone = next(
        (p for p in parts if re.search(r"\+?\d[\d\s-]{8,}", p)),
        "",
    )
    phone = re.sub(r"\s+", "", phone) if phone else ""
    linkedin = next((p for p in parts if "linkedin.com" in p.lower()), "")
    github = next((p for p in parts if "github.com" in p.lower()), "")
    if linkedin and not linkedin.startswith("http"):
        linkedin = "https://" + linkedin
    if github and not github.startswith("http"):
        github = "https://" + github
    return {
        "name": name,
        "location": location,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
    }


def fill_template(
    template: dict[str, Any],
    *,
    basics: dict[str, str],
    summary: str,
    jobs: list[dict[str, Any]],
    skills: list[dict[str, Any]],
    certs: list[dict[str, str]],
    awards: list[dict[str, str]],
    education: dict[str, str],
    headline: str | None,
) -> dict[str, Any]:
    out = copy.deepcopy(template)

    out["basics"]["name"] = basics["name"]
    out["basics"]["email"] = basics["email"] or out["basics"].get("email", "")
    out["basics"]["phone"] = basics["phone"] or out["basics"].get("phone", "")
    out["basics"]["location"] = basics["location"] or out["basics"].get("location", "")
    if basics["linkedin"]:
        out["basics"]["website"] = {
            "url": basics["linkedin"],
            "label": "LinkedIn",
        }
    # Headline: first job title if not provided
    out["basics"]["headline"] = headline or (jobs[0]["position"] if jobs else "")

    if basics["github"]:
        cfs = out["basics"].get("customFields") or []
        if cfs:
            cfs[0]["text"] = basics["github"]
        else:
            out["basics"]["customFields"] = [
                {
                    "id": new_id(),
                    "icon": "acorn",
                    "text": basics["github"],
                    "link": "",
                }
            ]

    out["summary"]["content"] = f"<p>{esc_html(summary)}</p>"

    # Experience
    old_exp = out["sections"]["experience"]["items"]
    new_exp: list[dict[str, Any]] = []
    for i, job in enumerate(jobs):
        item = (
            copy.deepcopy(old_exp[i])
            if i < len(old_exp)
            else {
                "id": new_id(),
                "hidden": False,
                "website": {"url": "", "label": "", "inlineLink": False},
                "roles": [],
            }
        )
        item.update(
            {
                "hidden": False,
                "company": job["company"],
                "position": job["position"],
                "location": job["location"],
                "period": job["period"],
                "description": job["description"],
            }
        )
        new_exp.append(item)
    out["sections"]["experience"]["items"] = new_exp

    # Skills (only tailored groups)
    old_skills = out["sections"]["skills"]["items"]
    new_skills: list[dict[str, Any]] = []
    for i, sk in enumerate(skills):
        item = (
            copy.deepcopy(old_skills[i])
            if i < len(old_skills)
            else {
                "id": new_id(),
                "hidden": False,
                "icon": "star",
                "iconColor": "",
                "proficiency": "",
                "level": 0,
            }
        )
        item["hidden"] = False
        item["name"] = sk["name"]
        item["keywords"] = sk["keywords"]
        new_skills.append(item)
    out["sections"]["skills"]["items"] = new_skills

    # Education — single B.Tech-style row from markdown
    edu_template = (
        copy.deepcopy(out["sections"]["education"]["items"][0])
        if out["sections"]["education"]["items"]
        else {
            "id": new_id(),
            "hidden": False,
            "website": {"url": "", "label": "", "inlineLink": False},
            "description": "",
            "location": "",
        }
    )
    edu_template.update(
        {
            "hidden": False,
            "school": education["school"],
            "degree": education["degree"],
            "area": education["area"],
            "grade": education["grade"],
            "period": education["period"],
            "description": "",
        }
    )
    out["sections"]["education"]["items"] = [edu_template]

    # Certifications
    old_certs = out["sections"]["certifications"]["items"]
    new_certs: list[dict[str, Any]] = []
    for i, c in enumerate(certs):
        item = (
            copy.deepcopy(old_certs[i])
            if i < len(old_certs)
            else {
                "id": new_id(),
                "hidden": False,
                "issuer": "",
                "website": {"url": "", "label": "", "inlineLink": False},
                "description": "",
            }
        )
        item.update(
            {
                "hidden": False,
                "title": c["title"],
                "date": c["date"],
                "issuer": c["issuer"],
                "description": "",
            }
        )
        new_certs.append(item)
    out["sections"]["certifications"]["items"] = new_certs

    # Awards
    old_awards = out["sections"]["awards"]["items"]
    new_awards: list[dict[str, Any]] = []
    for i, a in enumerate(awards):
        item = (
            copy.deepcopy(old_awards[i])
            if i < len(old_awards)
            else {
                "id": new_id(),
                "hidden": False,
                "website": {"url": "", "label": "", "inlineLink": False},
            }
        )
        item.update(
            {
                "hidden": False,
                "title": a["title"],
                "awarder": a["awarder"],
                "date": a["date"],
                "description": a["description"],
            }
        )
        new_awards.append(item)
    out["sections"]["awards"]["items"] = new_awards

    # Layout: experience before education (reader skim)
    pages = out.get("metadata", {}).get("layout", {}).get("pages", [])
    if pages:
        main = pages[0].get("main", [])
        if "experience" in main and "education" in main:
            without = [x for x in main if x not in ("experience", "education")]
            # insert after summary if present
            if "summary" in without:
                idx = without.index("summary") + 1
                without[idx:idx] = ["experience", "education"]
            else:
                without = ["experience", "education"] + without
            pages[0]["main"] = without

    return out


def infer_company_and_role(md_path: Path) -> tuple[str, str | None]:
    """
    Derive company (and optional role) from the markdown path.

    Supported layouts (first match wins):
      .../jobs/<company>/<role>/tailored-resume.md
      .../jobs/<company>/tailored-resume.md
      .../<company>/<role>/tailored-resume.md   # role folder is last path segment before file
      .../<company>/tailored-resume.md
    """
    path = md_path.resolve()
    parts = list(path.parts)
    reserved = {
        "reactive-resume",
        "output",
        "tools",
        "scripts",
        "templates",
        "md-to-reactive-resume",
        "resume-tools",
        "resume-agent-skills",
        ".cursor",
        "skills",
    }

    def looks_like_role(segment: str) -> bool:
        s = segment.lower()
        if s in {"em", "eng-manager", "engineering-manager", "manager", "swe", "staff", "principal"}:
            return True
        # hyphenated role slugs often have 2+ hyphens or end with -manager/-engineer
        if s.endswith(("-manager", "-engineer", "-lead", "-director", "-em")):
            return True
        return False

    if "jobs" in parts:
        i = parts.index("jobs")
        if i + 1 >= len(parts) - 1:
            raise ValueError(
                f"Path has 'jobs' but no company segment: {path}"
            )
        company = parts[i + 1]
        role: str | None = None
        if i + 2 < len(parts) - 1:
            role = parts[i + 2]
        return company, role

    parent = path.parent.name
    grandparent = path.parent.parent.name if path.parent.parent != path.parent else ""

    if parent.lower() not in reserved and parent not in {".", ""}:
        if looks_like_role(parent) and grandparent.lower() not in reserved and grandparent:
            return grandparent, parent
        return parent, None

    if grandparent.lower() not in reserved and grandparent:
        return grandparent, None

    raise ValueError(
        f"Could not infer company from path {path}. "
        "Put the file under jobs/<company>/... or pass --company."
    )


def convert(
    md_path: Path,
    template_path: Path,
    out_root: Path,
    company: str | None = None,
    role_slug: str | None = None,
    name_slug: str = "abhishek-das",
    headline: str | None = None,
) -> dict[str, Any]:
    md = md_path.read_text(encoding="utf-8")
    template = json.loads(template_path.read_text(encoding="utf-8"))

    inferred_company, inferred_role = None, None
    if company is None or role_slug is None:
        inferred_company, inferred_role = infer_company_and_role(md_path)

    company_value = company or inferred_company
    if not company_value:
        raise ValueError("Company is required (pass --company or use a path that includes it).")
    company_slug = slugify_company(company_value)

    # role: explicit flag > path inference > default em
    if role_slug:
        resolved_role = role_slug
    elif inferred_role:
        resolved_role = slugify_company(inferred_role)  # same slug rules
    else:
        resolved_role = "em"

    basics = parse_basics(md)
    summary = parse_summary(md)
    jobs = parse_jobs(md)
    skills = parse_skills(md)
    certs = parse_certifications(md)
    awards = parse_awards(md)
    education = parse_education(md)

    data = fill_template(
        template,
        basics=basics,
        summary=summary,
        jobs=jobs,
        skills=skills,
        certs=certs,
        awards=awards,
        education=education,
        headline=headline,
    )

    resume_basename = f"{name_slug}-{resolved_role}-{company_slug}"
    out_dir = out_root / company_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{resume_basename}.json"
    out_file.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {
        "path": out_file,
        "data": data,
        "name": resume_basename,
        "slug": resume_basename,
        "company_slug": company_slug,
        "role_slug": resolved_role,
        "tags": [company_slug, resolved_role],
    }


def load_env_file(path: Path) -> None:
    """Load KEY=VALUE lines into os.environ (does not override existing)."""
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


def resolve_api_key() -> str:
    tool_root = Path(__file__).resolve().parent.parent
    repo_root = tool_root.parent.parent  # resume-agent-skills/
    load_env_file(tool_root / ".env")
    load_env_file(repo_root / ".env")
    key = (
        os.environ.get("RXRESU_API_KEY")
        or os.environ.get("REACTIVE_RESUME_API_KEY")
        or ""
    ).strip()
    if not key:
        # Plain key file (single line) — preferred local drop for Cursor users
        for candidate in (
            tool_root / "reactive-resume-api-key.txt",
            tool_root / ".rxresu_api_key",
        ):
            if candidate.is_file():
                key = candidate.read_text(encoding="utf-8").strip().splitlines()[0].strip()
                if key:
                    break
    if not key:
        raise ValueError(
            "Missing API key. Set RXRESU_API_KEY (env or "
            "tools/md-to-reactive-resume/.env), or put the key in "
            "tools/md-to-reactive-resume/reactive-resume-api-key.txt. "
            "Create a key at https://rxresu.me → Settings → API Keys. "
            "Docs: https://docs.rxresu.me/guides/using-the-api"
        )
    return key


def api_request(
    method: str,
    url: str,
    api_key: str,
    payload: Any | None = None,
) -> Any:
    import urllib.error
    import urllib.request

    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {method} {url}: {detail}") from e


def upload_resume(
    resume_data: dict[str, Any],
    *,
    name: str,
    slug: str,
    tags: list[str],
    api_base: str = "https://rxresu.me/api/openapi",
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    Import ResumeData via POST /resumes/import, then PUT name/slug/tags.
    Returns {id, name, slug, dashboard_hint}.
    """
    key = api_key or resolve_api_key()
    base = api_base.rstrip("/")

    imported = api_request(
        "POST",
        f"{base}/resumes/import",
        key,
        {"data": resume_data},
    )
    # API returns the resume id as a JSON string
    resume_id = imported if isinstance(imported, str) else (
        imported.get("id") if isinstance(imported, dict) else None
    )
    if not resume_id:
        raise RuntimeError(f"Import did not return a resume id: {imported!r}")

    final_slug = slug
    updated = None
    last_err: Exception | None = None
    for attempt in range(0, 5):
        candidate = slug if attempt == 0 else f"{slug}-{attempt + 1}"
        try:
            updated = api_request(
                "PUT",
                f"{base}/resumes/{resume_id}",
                key,
                {
                    "name": name if attempt == 0 else f"{name}-{attempt + 1}",
                    "slug": candidate,
                    "tags": tags,
                },
            )
            final_slug = candidate
            break
        except RuntimeError as e:
            last_err = e
            if "RESUME_SLUG_ALREADY_EXISTS" not in str(e) and "slug" not in str(e).lower():
                raise
    if updated is None:
        raise RuntimeError(f"Could not set resume name/slug: {last_err}")

    return {
        "id": resume_id,
        "name": updated.get("name") if isinstance(updated, dict) else name,
        "slug": updated.get("slug") if isinstance(updated, dict) else final_slug,
        "dashboard": "https://rxresu.me/dashboard/resumes",
        "builder_hint": f"https://rxresu.me/dashboard/resumes (open resume id {resume_id})",
    }


def build_parser() -> argparse.ArgumentParser:
    here = Path(__file__).resolve().parent
    tool_root = here.parent
    repo_root = tool_root.parent.parent  # resume-agent-skills/
    default_template = tool_root / "templates" / "reactive-resume-base.json"
    default_out = repo_root / "output"

    p = argparse.ArgumentParser(
        description="Convert tailored-resume.md to Reactive Resume JSON (deterministic)."
    )
    p.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to tailored-resume.md (company inferred from parent folders if --company omitted)",
    )
    p.add_argument(
        "--company",
        "-c",
        default=None,
        help="Company name or slug (optional; inferred from path when omitted)",
    )
    p.add_argument(
        "--role",
        default=None,
        help="Role slug in filename (optional; inferred from path, else em)",
    )
    p.add_argument(
        "--name-slug",
        default="abhishek-das",
        help="Name slug prefix (default: abhishek-das)",
    )
    p.add_argument(
        "--headline",
        default=None,
        help="Optional basics.headline override (default: first job title)",
    )
    p.add_argument(
        "--template",
        type=Path,
        default=default_template,
        help="Reactive Resume base JSON template",
    )
    p.add_argument(
        "--out-root",
        type=Path,
        default=default_out,
        help="Output root; creates <out-root>/<company-slug>/",
    )
    p.add_argument(
        "--upload",
        action="store_true",
        help="Upload to Reactive Resume via API (requires RXRESU_API_KEY)",
    )
    p.add_argument(
        "--no-upload",
        action="store_true",
        help="Skip upload even if skill defaults expect it",
    )
    p.add_argument(
        "--api-base",
        default="https://rxresu.me/api/openapi",
        help="Reactive Resume OpenAPI base URL",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.input.is_file():
        print(f"Input not found: {args.input}", file=sys.stderr)
        return 1
    if not args.template.is_file():
        print(f"Template not found: {args.template}", file=sys.stderr)
        return 1
    try:
        result = convert(
            md_path=args.input.resolve(),
            template_path=args.template.resolve(),
            out_root=args.out_root.resolve(),
            company=args.company,
            role_slug=args.role,
            name_slug=args.name_slug,
            headline=args.headline,
        )
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        return 1

    print(f"json: {result['path']}")

    do_upload = args.upload and not args.no_upload
    if do_upload:
        try:
            uploaded = upload_resume(
                result["data"],
                name=result["name"],
                slug=result["slug"],
                tags=result["tags"],
                api_base=args.api_base,
            )
        except Exception as e:
            print(f"Upload failed: {e}", file=sys.stderr)
            return 2
        meta_path = result["path"].with_suffix(".upload.json")
        meta_path.write_text(
            json.dumps(uploaded, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"resume_id: {uploaded['id']}")
        print(f"name: {uploaded['name']}")
        print(f"slug: {uploaded['slug']}")
        print(f"dashboard: {uploaded['dashboard']}")
        print(f"upload_meta: {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
