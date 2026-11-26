"""Server-side PDF export.

ReportLab is used directly (no headless browser, no system fonts to install), producing a
single-column A4 document with selectable text so the export stays ATS-readable.
"""

from __future__ import annotations

import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from app.core.errors import Unprocessable
from app.services.builder import SECTION_TITLES


def _hex(value: str, fallback: str = "#1e293b") -> colors.Color:
    try:
        return colors.HexColor(value if value.startswith("#") else f"#{value}")
    except Exception:
        return colors.HexColor(fallback)


def _styles(accent: colors.Color) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "name": ParagraphStyle(
            "Name", parent=base["Title"], fontName="Helvetica-Bold", fontSize=20,
            leading=24, alignment=TA_LEFT, spaceAfter=2, textColor=colors.HexColor("#0f172a"),
        ),
        "headline": ParagraphStyle(
            "Headline", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10,
            leading=13, textColor=accent, spaceAfter=3,
        ),
        "contact": ParagraphStyle(
            "Contact", parent=base["Normal"], fontName="Helvetica", fontSize=8.5,
            leading=11, textColor=colors.HexColor("#475569"), spaceAfter=2,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=9.5,
            leading=12, textColor=accent, spaceBefore=9, spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["Normal"], fontName="Helvetica", fontSize=9.5,
            leading=12.5, textColor=colors.HexColor("#1f2937"),
        ),
        "muted": ParagraphStyle(
            "Muted", parent=base["Normal"], fontName="Helvetica", fontSize=8.5,
            leading=11, textColor=colors.HexColor("#64748b"),
        ),
    }


def _bullet_list(items: list[str], style: ParagraphStyle) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(str(item), style), leftIndent=10) for item in items if str(item).strip()],
        bulletType="bullet",
        start="•",
        leftIndent=12,
        bulletFontSize=7,
        spaceBefore=1,
        spaceAfter=2,
    )


def render_pdf(content: dict[str, Any], template: dict[str, Any] | None = None) -> bytes:
    template = template or {}
    layout = template.get("layout") or {}
    accent = _hex(str(layout.get("accent", "#1e293b")))
    styles = _styles(accent)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"{content.get('full_name', 'Resume')} — Resume",
        author=content.get("full_name", ""),
    )

    story: list[Any] = []
    story.append(Paragraph(str(content.get("full_name") or "Your Name"), styles["name"]))
    if content.get("headline"):
        story.append(Paragraph(str(content["headline"]), styles["headline"]))
    contact_parts = [
        str(content.get("email") or ""),
        str(content.get("phone") or ""),
        str(content.get("location") or ""),
        *[str(link) for link in content.get("links", [])],
    ]
    contact = "  ·  ".join(part for part in contact_parts if part.strip())
    if contact:
        story.append(Paragraph(contact, styles["contact"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.2, color=accent, spaceAfter=6))

    order = content.get("section_order") or list(SECTION_TITLES)
    custom = content.get("custom_sections") or {}

    for section in order:
        if section == "summary" and content.get("summary"):
            story += [Paragraph(SECTION_TITLES["summary"], styles["h2"]),
                      Paragraph(str(content["summary"]), styles["body"])]
        elif section == "skills" and content.get("skills"):
            story += [Paragraph(SECTION_TITLES["skills"], styles["h2"]),
                      Paragraph("  ·  ".join(str(s) for s in content["skills"]), styles["body"])]
        elif section == "experience" and content.get("experience"):
            story.append(Paragraph(SECTION_TITLES["experience"], styles["h2"]))
            for role in content["experience"]:
                title = str(role.get("title") or "")
                dates = " – ".join(p for p in [role.get("start_date", ""), role.get("end_date", "")] if p)
                story.append(Paragraph(f"<b>{title}</b>" + (f"  <font size=8 color='#64748b'>{dates}</font>" if dates else ""), styles["body"]))
                company = str(role.get("company") or "")
                if company:
                    story.append(Paragraph(company, styles["muted"]))
                if role.get("bullets"):
                    story.append(_bullet_list(role["bullets"], styles["body"]))
        elif section == "education" and content.get("education"):
            story.append(Paragraph(SECTION_TITLES["education"], styles["h2"]))
            for item in content["education"]:
                dates = " – ".join(p for p in [item.get("start_date", ""), item.get("end_date", "")] if p)
                story.append(Paragraph(f"<b>{item.get('degree', '')}</b>" + (f"  <font size=8 color='#64748b'>{dates}</font>" if dates else ""), styles["body"]))
                if item.get("institution"):
                    story.append(Paragraph(str(item["institution"]), styles["muted"]))
                if item.get("details"):
                    story.append(Paragraph(str(item["details"]), styles["body"]))
        elif section == "projects" and content.get("projects"):
            story.append(Paragraph(SECTION_TITLES["projects"], styles["h2"]))
            for project in content["projects"]:
                story.append(Paragraph(f"<b>{project.get('name', '')}</b>", styles["body"]))
                if project.get("description"):
                    story.append(Paragraph(str(project["description"]), styles["body"]))
                if project.get("technologies"):
                    story.append(Paragraph(", ".join(str(t) for t in project["technologies"]), styles["muted"]))
        elif section in {"certifications", "achievements", "languages"} and content.get(section):
            story += [Paragraph(SECTION_TITLES[section], styles["h2"]),
                      _bullet_list(list(content[section]), styles["body"])]
        elif section in custom and custom[section]:
            story += [Paragraph(str(section), styles["h2"]), _bullet_list(list(custom[section]), styles["body"])]

    try:
        doc.build(story)
    except Exception as exc:  # malformed content should not 500 the API
        raise Unprocessable("The resume could not be rendered to PDF", code="PDF_RENDER_FAILED") from exc
    return buffer.getvalue()
