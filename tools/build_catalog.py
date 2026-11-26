"""Generate the reference data for ResumeIQ.

Two outputs, one source of truth:
  supabase/seed.sql                            plans, career domains, skills, domain skills, templates
  backend/app/services/taxonomy_catalog.py     the same vocabulary for the offline AI provider

Run from the repository root:

    python tools/build_catalog.py

Both files are committed so a fresh clone works without running this script.
"""

import json

def q(s):
    if s is None: return "null"
    return "'" + str(s).replace("'", "''") + "'"

def arr(items):
    if not items: return "'{}'"
    return "array[" + ", ".join(q(i) for i in items) + "]"

plans = [
    ("free", "Free", "Try the core analysis on one or two resumes a month.", 0, 0, 2, 2,
     {"jd_matching": False, "ai_rewrite": False, "version_compare": False, "templates": ["ats-friendly", "minimalist"], "priority_queue": False, "exports": 2}),
    ("pro", "Pro", "For active job seekers who tailor a resume per application.", 1200, 11500, 20, 10,
     {"jd_matching": True, "ai_rewrite": True, "version_compare": True, "templates": ["ats-friendly", "minimalist", "modern-professional", "software-developer", "fresh-graduate"], "priority_queue": False, "exports": 25}),
    ("premium", "Premium", "For senior candidates and career changers running many searches.", 2900, 27900, 60, 30,
     {"jd_matching": True, "ai_rewrite": True, "version_compare": True, "templates": ["ats-friendly", "minimalist", "modern-professional", "software-developer", "fresh-graduate", "experienced-professional", "creative-designer"], "priority_queue": True, "exports": 100}),
]

# (canonical, kind, category, aliases)
skills = [
    ("HTML5", "technical", "frontend", ["HTML", "HTML 5"]),
    ("CSS3", "technical", "frontend", ["CSS", "CSS 3"]),
    ("JavaScript", "technical", "frontend", ["JS", "ES6", "ECMAScript", "JavaScript ES6"]),
    ("TypeScript", "technical", "frontend", ["TS"]),
    ("React.js", "technical", "frontend", ["React", "ReactJS", "React JS"]),
    ("Next.js", "technical", "frontend", ["NextJS", "Next JS"]),
    ("Vue.js", "technical", "frontend", ["Vue", "VueJS"]),
    ("Angular", "technical", "frontend", ["AngularJS"]),
    ("Redux", "technical", "frontend", ["Redux Toolkit", "RTK"]),
    ("Tailwind CSS", "technical", "frontend", ["Tailwind", "TailwindCSS"]),
    ("Responsive Design", "technical", "frontend", ["Responsive Web Design", "Mobile First Design"]),
    ("Accessibility", "technical", "frontend", ["a11y", "WCAG"]),
    ("REST APIs", "technical", "backend", ["REST", "RESTful APIs", "REST API"]),
    ("GraphQL", "technical", "backend", ["Graph QL", "Apollo"]),
    ("Node.js", "technical", "backend", ["Node", "NodeJS"]),
    ("Express.js", "technical", "backend", ["Express", "ExpressJS"]),
    ("Python", "technical", "backend", ["Python 3"]),
    ("FastAPI", "technical", "backend", ["Fast API"]),
    ("Django", "technical", "backend", []),
    ("Flask", "technical", "backend", []),
    ("Java", "technical", "backend", ["Java 8", "Java 17"]),
    ("Spring Boot", "technical", "backend", ["Spring"]),
    ("C#", "technical", "backend", ["CSharp", "C Sharp"]),
    ("ASP.NET", "technical", "backend", ["ASP.NET Core", "dotnet", ".NET"]),
    ("PHP", "technical", "backend", ["PHP 8"]),
    ("Laravel", "technical", "backend", []),
    ("Go", "technical", "backend", ["Golang"]),
    ("SQL", "technical", "data", ["Structured Query Language"]),
    ("PostgreSQL", "technical", "data", ["Postgres", "psql"]),
    ("MySQL", "technical", "data", []),
    ("MongoDB", "technical", "data", ["Mongo"]),
    ("Redis", "technical", "data", []),
    ("Database Design", "technical", "data", ["Schema Design", "Normalization", "Data Modeling"]),
    ("Pandas", "technical", "data", []),
    ("NumPy", "technical", "data", ["Numpy"]),
    ("Scikit-learn", "technical", "data", ["sklearn", "Scikit Learn"]),
    ("TensorFlow", "technical", "data", ["TF"]),
    ("PyTorch", "technical", "data", []),
    ("Machine Learning", "technical", "data", ["ML", "Statistical Learning"]),
    ("Data Visualization", "technical", "data", ["Data Visualisation", "Dashboards"]),
    ("Statistics", "technical", "data", ["Statistical Analysis", "Probability"]),
    ("Excel", "tool", "data", ["Microsoft Excel", "Advanced Excel"]),
    ("Power BI", "tool", "data", ["PowerBI"]),
    ("Tableau", "tool", "data", []),
    ("Git", "tool", "engineering", ["Version Control"]),
    ("GitHub", "tool", "engineering", ["Git Hub"]),
    ("Docker", "tool", "engineering", ["Containerization", "Containers"]),
    ("Kubernetes", "tool", "engineering", ["K8s"]),
    ("CI/CD", "tool", "engineering", ["Continuous Integration", "Continuous Delivery", "GitHub Actions", "Jenkins"]),
    ("Linux", "tool", "engineering", ["Ubuntu", "Unix", "Bash", "Shell Scripting"]),
    ("AWS", "tool", "engineering", ["Amazon Web Services", "EC2", "S3", "Lambda"]),
    ("Azure", "tool", "engineering", ["Microsoft Azure"]),
    ("Google Cloud", "tool", "engineering", ["GCP"]),
    ("Terraform", "tool", "engineering", ["Infrastructure as Code", "IaC"]),
    ("Nginx", "tool", "engineering", []),
    ("Jest", "tool", "testing", ["Unit Testing", "Vitest"]),
    ("Pytest", "tool", "testing", ["PyTest"]),
    ("Selenium", "tool", "testing", ["Playwright", "Cypress", "End-to-End Testing"]),
    ("Figma", "tool", "design", ["Figma Design"]),
    ("Adobe Photoshop", "tool", "design", ["Photoshop"]),
    ("Adobe Illustrator", "tool", "design", ["Illustrator"]),
    ("Sketch", "tool", "design", []),
    ("User Research", "technical", "design", ["UX Research", "Usability Testing", "Interviews"]),
    ("Wireframing", "technical", "design", ["Wireframes", "Prototyping", "Prototypes"]),
    ("Design Systems", "technical", "design", ["Component Library", "UI Kit"]),
    ("Typography", "technical", "design", ["Type Hierarchy"]),
    ("Brand Identity", "technical", "design", ["Branding", "Logo Design"]),
    ("Penetration Testing", "technical", "security", ["Pen Testing", "Ethical Hacking", "Pentesting"]),
    ("Network Security", "technical", "security", ["Firewalls", "IDS", "IPS"]),
    ("OWASP", "technical", "security", ["OWASP Top 10", "Web Application Security"]),
    ("Cryptography", "technical", "security", ["Encryption", "TLS"]),
    ("Incident Response", "technical", "security", ["Forensics", "SIEM"]),
    ("SEO", "technical", "marketing", ["Search Engine Optimization", "On-page SEO"]),
    ("Google Analytics", "tool", "marketing", ["GA4", "Web Analytics"]),
    ("Content Marketing", "technical", "marketing", ["Copywriting", "Content Strategy"]),
    ("Email Marketing", "technical", "marketing", ["Mailchimp", "Campaigns"]),
    ("Paid Advertising", "technical", "marketing", ["Google Ads", "Meta Ads", "PPC"]),
    ("Social Media Marketing", "technical", "marketing", ["SMM", "Social Media"]),
    ("Market Research", "technical", "business", ["Competitive Analysis"]),
    ("Business Process Modeling", "technical", "business", ["BPMN", "Process Mapping"]),
    ("Requirements Gathering", "technical", "business", ["Elicitation", "BRD", "User Stories"]),
    ("Stakeholder Management", "soft", "business", ["Stakeholder Communication"]),
    ("Agile", "technical", "business", ["Scrum", "Kanban", "Sprint Planning"]),
    ("Jira", "tool", "business", ["Atlassian Jira"]),
    ("Project Planning", "technical", "business", ["Roadmapping", "Gantt", "Timeline Planning"]),
    ("Risk Management", "technical", "business", ["Risk Assessment"]),
    ("Communication", "soft", "interpersonal", ["Written Communication", "Verbal Communication"]),
    ("Teamwork", "soft", "interpersonal", ["Collaboration", "Cross-functional Collaboration"]),
    ("Problem Solving", "soft", "interpersonal", ["Analytical Thinking", "Critical Thinking"]),
    ("Leadership", "soft", "interpersonal", ["Team Leadership", "Mentoring"]),
    ("Time Management", "soft", "interpersonal", ["Prioritization", "Deadline Management"]),
    ("Adaptability", "soft", "interpersonal", ["Flexibility"]),
    ("Attention to Detail", "soft", "interpersonal", ["Detail Oriented"]),
    ("Presentation Skills", "soft", "interpersonal", ["Public Speaking", "Demoing"]),
]

domains = [
    ("frontend-developer", "Frontend Developer", "Interfaces, component architecture and browser performance.", "layout",
     {"required": ["HTML5", "CSS3", "JavaScript", "React.js", "Git", "Responsive Design", "REST APIs"],
      "preferred": ["TypeScript", "Redux", "Tailwind CSS", "Accessibility", "Jest"],
      "optional": ["Next.js", "Figma", "Design Systems", "Vue.js"]}),
    ("backend-developer", "Backend Developer", "APIs, data modelling, reliability and server-side logic.", "server",
     {"required": ["REST APIs", "SQL", "Git", "Database Design", "Python", "Node.js"],
      "preferred": ["PostgreSQL", "Docker", "Redis", "FastAPI", "Express.js", "Linux"],
      "optional": ["GraphQL", "Kubernetes", "AWS", "CI/CD"]}),
    ("full-stack-developer", "Full-Stack Developer", "End-to-end product delivery across client and server.", "layers",
     {"required": ["JavaScript", "React.js", "REST APIs", "SQL", "Git", "HTML5", "CSS3"],
      "preferred": ["TypeScript", "Node.js", "PostgreSQL", "Docker", "Database Design"],
      "optional": ["Next.js", "CI/CD", "AWS", "Redis"]}),
    ("react-developer", "React.js Developer", "Deep React expertise: state, rendering and component design.", "atom",
     {"required": ["HTML5", "CSS3", "JavaScript", "React.js", "TypeScript", "Redux", "REST APIs", "Git"],
      "preferred": ["Responsive Design", "Jest", "Tailwind CSS", "Accessibility"],
      "optional": ["Next.js", "GraphQL", "Design Systems", "Figma"]}),
    ("python-developer", "Python Developer", "Python services, automation, data pipelines and scripting.", "code",
     {"required": ["Python", "Git", "SQL", "REST APIs"],
      "preferred": ["FastAPI", "Django", "Pandas", "Docker", "PostgreSQL", "Linux"],
      "optional": ["Redis", "AWS", "Pytest", "Celery" if False else "NumPy"]}),
    ("java-developer", "Java Developer", "JVM services, enterprise integration and concurrency.", "coffee",
     {"required": ["Java", "SQL", "Git", "REST APIs", "Spring Boot"],
      "preferred": ["PostgreSQL", "Docker", "CI/CD", "Database Design"],
      "optional": ["Kubernetes", "AWS", "Redis", "Agile"]}),
    ("software-engineer", "Software Engineer", "Generalist engineering: design, build, test, operate.", "cpu",
     {"required": ["Git", "SQL", "REST APIs", "Problem Solving", "Communication"],
      "preferred": ["Python", "JavaScript", "Docker", "Database Design", "CI/CD", "Agile"],
      "optional": ["Kubernetes", "AWS", "Redis", "TypeScript"]}),
    ("ui-ux-designer", "UI/UX Designer", "Research, flows, interface design and design systems.", "pen-tool",
     {"required": ["Figma", "User Research", "Wireframing", "Design Systems", "Communication"],
      "preferred": ["Accessibility", "Typography", "HTML5", "CSS3"],
      "optional": ["Adobe Illustrator", "Adobe Photoshop", "Sketch"]}),
    ("graphic-designer", "Graphic Designer", "Visual identity, layout and brand communication.", "palette",
     {"required": ["Adobe Photoshop", "Adobe Illustrator", "Typography", "Brand Identity"],
      "preferred": ["Figma", "Design Systems", "Communication", "Attention to Detail"],
      "optional": ["Adobe Photoshop", "Social Media Marketing", "Market Research"]}),
    ("data-analyst", "Data Analyst", "Turn data into decisions: SQL, dashboards and clear reporting.", "bar-chart",
     {"required": ["SQL", "Excel", "Data Visualization", "Statistics", "Communication"],
      "preferred": ["Python", "Power BI", "Tableau", "Pandas", "Database Design"],
      "optional": ["Machine Learning", "Google Analytics", "Market Research"]}),
    ("data-scientist", "Data Scientist", "Modelling, experimentation and production ML.", "brain",
     {"required": ["Python", "Statistics", "Machine Learning", "Pandas", "SQL"],
      "preferred": ["Scikit-learn", "NumPy", "Data Visualization", "Git"],
      "optional": ["TensorFlow", "PyTorch", "Docker", "AWS"]}),
    ("cybersecurity-engineer", "Cybersecurity Engineer", "Harden systems, test defences and respond to incidents.", "shield",
     {"required": ["Network Security", "OWASP", "Linux", "Penetration Testing"],
      "preferred": ["Cryptography", "Incident Response", "Python", "Docker"],
      "optional": ["AWS", "Kubernetes", "CI/CD", "Communication"]}),
    ("devops-engineer", "DevOps Engineer", "Automate build, release and infrastructure with observability.", "infinity",
     {"required": ["Linux", "Docker", "CI/CD", "Git", "AWS"],
      "preferred": ["Kubernetes", "Terraform", "Python", "Nginx", "Redis"],
      "optional": ["PostgreSQL", "Network Security", "Incident Response"]}),
    ("digital-marketer", "Digital Marketer", "Acquisition, content and lifecycle marketing with measurable ROI.", "megaphone",
     {"required": ["SEO", "Google Analytics", "Content Marketing", "Social Media Marketing"],
      "preferred": ["Email Marketing", "Paid Advertising", "Market Research", "Communication"],
      "optional": ["Adobe Photoshop", "Data Visualization", "Excel"]}),
    ("business-analyst", "Business Analyst", "Translate business needs into testable requirements.", "clipboard",
     {"required": ["Requirements Gathering", "Business Process Modeling", "Stakeholder Management", "SQL", "Communication"],
      "preferred": ["Agile", "Jira", "Excel", "Data Visualization"],
      "optional": ["Power BI", "Project Planning", "Market Research"]}),
    ("project-manager", "Project Manager", "Plan, coordinate and deliver across teams and constraints.", "calendar",
     {"required": ["Project Planning", "Stakeholder Management", "Risk Management", "Agile", "Communication"],
      "preferred": ["Jira", "Time Management", "Leadership", "Excel"],
      "optional": ["SQL", "Business Process Modeling", "Data Visualization"]}),
]

templates = [
    ("ats-friendly", "ATS-Friendly", "Single column, standard headings, no graphics. Maximum parser compatibility.", "free", True, {"columns": 1, "accent": "#1e293b", "font": "Inter", "show_photo": False, "section_order": ["summary", "skills", "experience", "education", "projects", "certifications"]}),
    ("modern-professional", "Modern Professional", "Two-column header with a subtle accent rule. Balanced for corporate roles.", "pro", True, {"columns": 1, "accent": "#4338ca", "font": "Inter", "show_photo": False, "section_order": ["summary", "experience", "skills", "education", "projects", "certifications"]}),
    ("software-developer", "Software Developer", "Technical skills grid above experience, project-first for engineers.", "pro", True, {"columns": 1, "accent": "#0f766e", "font": "JetBrains Mono", "show_photo": False, "section_order": ["summary", "skills", "projects", "experience", "education", "certifications"]}),
    ("fresh-graduate", "Fresh Graduate", "Education and coursework lead, projects carry the weight.", "pro", True, {"columns": 1, "accent": "#2563eb", "font": "Inter", "show_photo": False, "section_order": ["summary", "education", "projects", "skills", "experience", "achievements"]}),
    ("experienced-professional", "Experienced Professional", "Achievement-dense experience section for 5+ years.", "premium", True, {"columns": 1, "accent": "#334155", "font": "Source Serif", "show_photo": False, "section_order": ["summary", "experience", "achievements", "skills", "education", "certifications"]}),
    ("creative-designer", "Creative Designer", "Asymmetric header, strong type hierarchy, still single column body.", "premium", False, {"columns": 1, "accent": "#be185d", "font": "Playfair Display", "show_photo": True, "section_order": ["summary", "skills", "projects", "experience", "education", "achievements"]}),
    ("minimalist", "Minimalist", "Quiet typography, generous whitespace, no rules or boxes.", "free", True, {"columns": 1, "accent": "#111827", "font": "Inter", "show_photo": False, "section_order": ["summary", "experience", "education", "skills", "projects"]}),
]

out = []
out.append("-- ResumeIQ seed: reference data only. No fake users or fake resumes.")
out.append("-- Idempotent: safe to re-run with `supabase db reset` or `psql -f`.\n")

out.append("-- Plans")
for code, name, desc, monthly, annual, quota, max_res, features in plans:
    out.append(
        f"insert into subscription_plans (code, name, description, monthly_price_cents, annual_price_cents, analysis_quota, max_resumes, features, sort_order)\n"
        f"values ({q(code)}, {q(name)}, {q(desc)}, {monthly}, {annual}, {quota}, {max_res}, {q(json.dumps(features))}::jsonb, {plans.index((code,name,desc,monthly,annual,quota,max_res,features))})\n"
        f"on conflict (code) do update set name = excluded.name, description = excluded.description, monthly_price_cents = excluded.monthly_price_cents, annual_price_cents = excluded.annual_price_cents, analysis_quota = excluded.analysis_quota, max_resumes = excluded.max_resumes, features = excluded.features;"
    )
out.append("")

out.append("-- Career domains")
for i, (slug, name, desc, icon, _) in enumerate(domains):
    out.append(
        f"insert into career_domains (slug, name, description, icon, sort_order) values ({q(slug)}, {q(name)}, {q(desc)}, {q(icon)}, {i})\n"
        f"on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;"
    )
out.append("")

out.append("-- Skills")
for canonical, kind, category, aliases in skills:
    out.append(
        f"insert into skills (canonical_name, aliases, kind, category) values ({q(canonical)}, {arr(aliases)}, {q(kind)}::skill_kind, {q(category)})\n"
        f"on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;"
    )
out.append("")

out.append("-- Domain skill mapping")
weights = {"required": 3.0, "preferred": 1.5, "optional": 0.5}
for slug, name, desc, icon, mapping in domains:
    for level in ("required", "preferred", "optional"):
        for skill in mapping[level]:
            out.append(
                f"insert into domain_skills (domain_id, skill_id, requirement, weight)\n"
                f"select d.id, s.id, {q(level)}::requirement_level, {weights[level]}\n"
                f"from career_domains d, skills s where d.slug = {q(slug)} and s.canonical_name = {q(skill)}\n"
                f"on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;"
            )
out.append("")

out.append("-- Templates")
for i, (slug, name, desc, tier, ats, layout) in enumerate(templates):
    out.append(
        f"insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ({q(slug)}, {q(name)}, {q(desc)}, {q(tier)}::template_tier, {str(ats).lower()}, {q(json.dumps(layout))}::jsonb, {i})\n"
        f"on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;"
    )
out.append("")

out.append("""-- Default scoring weights (admin-editable)
insert into app_settings (key, value)
values ('scoring_weights', '{"keyword_match": 20, "technical_skills": 20, "ats_compatibility": 15, "content_quality": 15, "grammar": 10, "formatting": 10, "experience_relevance": 10}'::jsonb)
on conflict (key) do nothing;
""")

open("supabase/seed.sql", "w").write("\n".join(out) + "\n")
print("seed.sql lines:", len(out))
print("skills:", len(skills), "domains:", len(domains), "templates:", len(templates))

# --- also emit the offline taxonomy catalog used by the deterministic AI provider ---
lines = [
    '"""Static mirror of the seeded skill taxonomy.',
    "",
    "The deterministic AI provider needs the skill vocabulary without a database connection.",
    "This file is generated from the same source as supabase/seed.sql; keep them in step",
    "(`python tools/build_catalog.py`).",
    '"""',
    "",
    "from __future__ import annotations",
    "",
    "CATALOG: list[dict[str, object]] = [",
]
for canonical, kind, category, aliases in skills:
    lines.append(
        "    {"
        f"'canonical_name': {canonical!r}, 'aliases': {list(aliases)!r}, "
        f"'kind': {kind!r}, 'category': {category!r}"
        "},"
    )
lines.append("]")
lines.append("")
lines.append("DOMAIN_SKILLS: dict[str, dict[str, list[str]]] = {")
for slug, name, desc, icon, mapping in domains:
    lines.append(f"    {slug!r}: {{")
    for level in ("required", "preferred", "optional"):
        lines.append(f"        {level!r}: {mapping[level]!r},")
    lines.append("    },")
lines.append("}")
lines.append("")
open("backend/app/services/taxonomy_catalog.py", "w").write("\n".join(lines))
print("catalog written")
