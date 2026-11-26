"""Resume content model: defaults, extraction mapping, HTML rendering.

One content model feeds the live preview and the PDF export, so what the user sees is what the
recruiter receives.
"""

from __future__ import annotations

import html
from typing import Any

SECTION_TITLES = {
    "summary": "Professional Summary",
    "skills": "Skills",
    "experience": "Experience",
    "education": "Education",
    "projects": "Projects",
    "certifications": "Certifications",
    "achievements": "Achievements",
    "languages": "Languages",
}


def empty_content(full_name: str = "", email: str = "") -> dict[str, Any]:
    return {
        "full_name": full_name,
        "headline": "",
        "email": email,
        "phone": "",
        "location": "",
        "links": [],
        "summary": "",
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
        "certifications": [],
        "achievements": [],
        "languages": [],
        "custom_sections": {},
        "section_order": ["summary", "skills", "experience", "education", "projects"],
    }


def content_from_extracted(extracted: dict[str, Any], *, fallback_name: str = "") -> dict[str, Any]:
    content = empty_content(extracted.get("full_name") or fallback_name, extracted.get("email", ""))
    content.update(
        {
            "phone": extracted.get("phone", ""),
            "links": extracted.get("links", []),
            "summary": extracted.get("summary", ""),
            "skills": extracted.get("listed_skills", []),
            "experience": [
                {
                    "title": entry.get("title", ""),
                    "company": entry.get("company", ""),
                    "location": "",
                    "start_date": entry.get("start_date", ""),
                    "end_date": entry.get("end_date", ""),
                    "bullets": entry.get("bullets", []),
                }
                for entry in extracted.get("experience", [])
            ],
            "education": [
                {
                    "degree": entry.get("degree", ""),
                    "institution": entry.get("institution", ""),
                    "location": "",
                    "start_date": entry.get("start_date", ""),
                    "end_date": entry.get("end_date", ""),
                    "details": entry.get("details", ""),
                }
                for entry in extracted.get("education", [])
            ],
            "projects": [
                {
                    "name": entry.get("name", ""),
                    "description": entry.get("description", ""),
                    "link": entry.get("link", ""),
                    "technologies": [],
                }
                for entry in extracted.get("projects", [])
            ],
            "certifications": extracted.get("certifications", []),
            "achievements": extracted.get("achievements", []),
            "languages": extracted.get("languages", []),
        }
    )
    return content


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _date_range(start: str, end: str) -> str:
    if start and end:
        return f"{_esc(start)} – {_esc(end)}"
    return _esc(start or end)


def render_html(content: dict[str, Any], template: dict[str, Any] | None = None) -> str:
    """Single-column, ATS-readable HTML. Template controls accent and font only."""
    template = template or {}
    layout = template.get("layout") or {}
    accent = layout.get("accent", "#1e293b")
    font = layout.get("font", "Inter")
    order = content.get("section_order") or list(SECTION_TITLES)

    blocks: list[str] = []
    for section in order:
        if section == "summary" and content.get("summary"):
            blocks.append(
                f'<section><h2>{SECTION_TITLES["summary"]}</h2><p>{_esc(content["summary"])}</p></section>'
            )
        elif section == "skills" and content.get("skills"):
            items = "".join(f"<li>{_esc(skill)}</li>" for skill in content["skills"])
            blocks.append(f'<section><h2>{SECTION_TITLES["skills"]}</h2><ul class="inline">{items}</ul></section>')
        elif section == "experience" and content.get("experience"):
            roles = []
            for role in content["experience"]:
                bullets = "".join(f"<li>{_esc(b)}</li>" for b in role.get("bullets", []))
                roles.append(
                    '<div class="entry">'
                    f'<div class="entry-head"><strong>{_esc(role.get("title"))}</strong>'
                    f'<span>{_date_range(role.get("start_date", ""), role.get("end_date", ""))}</span></div>'
                    f'<div class="muted">{_esc(role.get("company"))}'
                    f'{" · " + _esc(role.get("location")) if role.get("location") else ""}</div>'
                    f"<ul>{bullets}</ul></div>"
                )
            blocks.append(f'<section><h2>{SECTION_TITLES["experience"]}</h2>{"".join(roles)}</section>')
        elif section == "education" and content.get("education"):
            entries = []
            for item in content["education"]:
                details = item.get("details")
                details_html = f"<p>{_esc(details)}</p>" if details else ""
                entries.append(
                    '<div class="entry">'
                    f'<div class="entry-head"><strong>{_esc(item.get("degree"))}</strong>'
                    f'<span>{_date_range(item.get("start_date", ""), item.get("end_date", ""))}</span></div>'
                    f'<div class="muted">{_esc(item.get("institution"))}</div>'
                    f"{details_html}"
                    "</div>"
                )
            blocks.append(f'<section><h2>{SECTION_TITLES["education"]}</h2>{"".join(entries)}</section>')
        elif section == "projects" and content.get("projects"):
            entries = []
            for project in content["projects"]:
                tech = ", ".join(project.get("technologies", []))
                tech_html = f'<div class="muted">{_esc(tech)}</div>' if tech else ""
                entries.append(
                    '<div class="entry">'
                    f'<div class="entry-head"><strong>{_esc(project.get("name"))}</strong>'
                    f'<span>{_esc(project.get("link"))}</span></div>'
                    f'<p>{_esc(project.get("description"))}</p>'
                    f"{tech_html}"
                    "</div>"
                )
            blocks.append(f'<section><h2>{SECTION_TITLES["projects"]}</h2>{"".join(entries)}</section>')
        elif section in {"certifications", "achievements", "languages"} and content.get(section):
            items = "".join(f"<li>{_esc(item)}</li>" for item in content[section])
            blocks.append(f'<section><h2>{SECTION_TITLES[section]}</h2><ul>{items}</ul></section>')
        elif section in (content.get("custom_sections") or {}):
            items = "".join(f"<li>{_esc(item)}</li>" for item in content["custom_sections"][section])
            blocks.append(f"<section><h2>{_esc(section)}</h2><ul>{items}</ul></section>")

    contact = " · ".join(
        part
        for part in [
            _esc(content.get("email")),
            _esc(content.get("phone")),
            _esc(content.get("location")),
            " · ".join(_esc(link) for link in content.get("links", [])),
        ]
        if part
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{_esc(content.get("full_name"))} — Resume</title>
<style>
  @page {{ size: A4; margin: 18mm 16mm; }}
  body {{ font-family: {font}, "Helvetica Neue", Arial, sans-serif; color:#111827; font-size:10.5pt; line-height:1.45; }}
  header {{ border-bottom:2px solid {accent}; padding-bottom:10px; margin-bottom:16px; }}
  h1 {{ font-size:22pt; margin:0 0 2px; letter-spacing:-0.02em; color:#0f172a; }}
  .headline {{ color:{accent}; font-weight:600; margin:0 0 6px; }}
  .contact {{ color:#475569; font-size:9.5pt; }}
  h2 {{ font-size:10.5pt; text-transform:uppercase; letter-spacing:0.08em; color:{accent};
        margin:16px 0 6px; border-bottom:1px solid #e2e8f0; padding-bottom:3px; }}
  section {{ page-break-inside:avoid; }}
  .entry {{ margin-bottom:10px; }}
  .entry-head {{ display:flex; justify-content:space-between; gap:12px; }}
  .entry-head span {{ color:#64748b; font-size:9pt; white-space:nowrap; }}
  .muted {{ color:#64748b; font-size:9.5pt; }}
  ul {{ margin:4px 0 0 16px; padding:0; }}
  ul.inline {{ list-style:none; margin:0; padding:0; display:flex; flex-wrap:wrap; gap:6px 14px; }}
  li {{ margin-bottom:3px; }}
  p {{ margin:4px 0; }}
</style></head>
<body>
  <header>
    <h1>{_esc(content.get("full_name") or "Your Name")}</h1>
    <p class="headline">{_esc(content.get("headline"))}</p>
    <div class="contact">{contact}</div>
  </header>
  {"".join(blocks)}
</body></html>"""
