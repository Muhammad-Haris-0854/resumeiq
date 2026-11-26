import type { ResumeContent } from "@/types";

/** Mirrors backend/app/services/builder.py so the preview matches the exported PDF. */

const TITLES: Record<string, string> = {
  summary: "Professional Summary",
  skills: "Skills",
  experience: "Experience",
  education: "Education",
  projects: "Projects",
  certifications: "Certifications",
  achievements: "Achievements",
  languages: "Languages",
};

function esc(value: string | null | undefined): string {
  return (value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function dateRange(start: string, end: string): string {
  if (start && end) return `${esc(start)} – ${esc(end)}`;
  return esc(start || end);
}

export function previewHtml(content: ResumeContent, accent = "#1e293b", font = "Inter"): string {
  const order = content.section_order?.length ? content.section_order : ["summary", "skills", "experience", "education", "projects"];
  const blocks: string[] = [];

  for (const section of order) {
    if (section === "summary" && content.summary) {
      blocks.push(`<section><h2>${TITLES.summary}</h2><p>${esc(content.summary)}</p></section>`);
    } else if (section === "skills" && content.skills.length) {
      blocks.push(`<section><h2>${TITLES.skills}</h2><ul class="inline">${content.skills.map((s) => `<li>${esc(s)}</li>`).join("")}</ul></section>`);
    } else if (section === "experience" && content.experience.length) {
      const roles = content.experience
        .map(
          (role) => `<div class="entry"><div class="head"><strong>${esc(role.title)}</strong><span>${dateRange(role.start_date, role.end_date)}</span></div>
          <div class="muted">${esc(role.company)}${role.location ? ` · ${esc(role.location)}` : ""}</div>
          <ul>${role.bullets.filter(Boolean).map((b) => `<li>${esc(b)}</li>`).join("")}</ul></div>`,
        )
        .join("");
      blocks.push(`<section><h2>${TITLES.experience}</h2>${roles}</section>`);
    } else if (section === "education" && content.education.length) {
      const items = content.education
        .map(
          (item) => `<div class="entry"><div class="head"><strong>${esc(item.degree)}</strong><span>${dateRange(item.start_date, item.end_date)}</span></div>
          <div class="muted">${esc(item.institution)}</div>${item.details ? `<p>${esc(item.details)}</p>` : ""}</div>`,
        )
        .join("");
      blocks.push(`<section><h2>${TITLES.education}</h2>${items}</section>`);
    } else if (section === "projects" && content.projects.length) {
      const items = content.projects
        .map(
          (project) => `<div class="entry"><div class="head"><strong>${esc(project.name)}</strong><span>${esc(project.link)}</span></div>
          <p>${esc(project.description)}</p>${project.technologies.length ? `<div class="muted">${esc(project.technologies.join(", "))}</div>` : ""}</div>`,
        )
        .join("");
      blocks.push(`<section><h2>${TITLES.projects}</h2>${items}</section>`);
    } else if (["certifications", "achievements", "languages"].includes(section)) {
      const list = content[section as "certifications" | "achievements" | "languages"];
      if (list.length) {
        blocks.push(`<section><h2>${TITLES[section]}</h2><ul>${list.map((item) => `<li>${esc(item)}</li>`).join("")}</ul></section>`);
      }
    } else if (content.custom_sections[section]?.length) {
      blocks.push(
        `<section><h2>${esc(section)}</h2><ul>${content.custom_sections[section]!.map((item) => `<li>${esc(item)}</li>`).join("")}</ul></section>`,
      );
    }
  }

  const contact = [content.email, content.phone, content.location, ...content.links].filter(Boolean).map(esc).join(" · ");

  return `<!doctype html><html><head><meta charset="utf-8"><style>
    *{box-sizing:border-box}
    body{font-family:${font},"Helvetica Neue",Arial,sans-serif;color:#111827;font-size:10.5pt;line-height:1.45;margin:0;padding:22px 26px;background:#fff}
    header{border-bottom:2px solid ${accent};padding-bottom:10px;margin-bottom:14px}
    h1{font-size:21pt;margin:0 0 2px;letter-spacing:-.02em;color:#0f172a}
    .headline{color:${accent};font-weight:600;margin:0 0 6px;font-size:10pt}
    .contact{color:#475569;font-size:9pt}
    h2{font-size:10pt;text-transform:uppercase;letter-spacing:.08em;color:${accent};margin:14px 0 5px;border-bottom:1px solid #e2e8f0;padding-bottom:3px}
    .entry{margin-bottom:9px}
    .head{display:flex;justify-content:space-between;gap:12px}
    .head span{color:#64748b;font-size:8.5pt;white-space:nowrap}
    .muted{color:#64748b;font-size:9pt}
    ul{margin:3px 0 0 15px;padding:0}
    ul.inline{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:4px 12px}
    li{margin-bottom:2px}
    p{margin:3px 0}
  </style></head><body>
    <header><h1>${esc(content.full_name) || "Your Name"}</h1>
    ${content.headline ? `<p class="headline">${esc(content.headline)}</p>` : ""}
    ${contact ? `<div class="contact">${contact}</div>` : ""}</header>
    ${blocks.join("")}
  </body></html>`;
}
