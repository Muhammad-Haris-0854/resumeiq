-- ResumeIQ seed: reference data only. No fake users or fake resumes.
-- Idempotent: safe to re-run with `supabase db reset` or `psql -f`.

-- Plans
insert into subscription_plans (code, name, description, monthly_price_cents, annual_price_cents, analysis_quota, max_resumes, features, sort_order)
values ('free', 'Free', 'Try the core analysis on one or two resumes a month.', 0, 0, 2, 2, '{"jd_matching": false, "ai_rewrite": false, "version_compare": false, "templates": ["ats-friendly", "minimalist"], "priority_queue": false, "exports": 2}'::jsonb, 0)
on conflict (code) do update set name = excluded.name, description = excluded.description, monthly_price_cents = excluded.monthly_price_cents, annual_price_cents = excluded.annual_price_cents, analysis_quota = excluded.analysis_quota, max_resumes = excluded.max_resumes, features = excluded.features;
insert into subscription_plans (code, name, description, monthly_price_cents, annual_price_cents, analysis_quota, max_resumes, features, sort_order)
values ('pro', 'Pro', 'For active job seekers who tailor a resume per application.', 1200, 11500, 20, 10, '{"jd_matching": true, "ai_rewrite": true, "version_compare": true, "templates": ["ats-friendly", "minimalist", "modern-professional", "software-developer", "fresh-graduate"], "priority_queue": false, "exports": 25}'::jsonb, 1)
on conflict (code) do update set name = excluded.name, description = excluded.description, monthly_price_cents = excluded.monthly_price_cents, annual_price_cents = excluded.annual_price_cents, analysis_quota = excluded.analysis_quota, max_resumes = excluded.max_resumes, features = excluded.features;
insert into subscription_plans (code, name, description, monthly_price_cents, annual_price_cents, analysis_quota, max_resumes, features, sort_order)
values ('premium', 'Premium', 'For senior candidates and career changers running many searches.', 2900, 27900, 60, 30, '{"jd_matching": true, "ai_rewrite": true, "version_compare": true, "templates": ["ats-friendly", "minimalist", "modern-professional", "software-developer", "fresh-graduate", "experienced-professional", "creative-designer"], "priority_queue": true, "exports": 100}'::jsonb, 2)
on conflict (code) do update set name = excluded.name, description = excluded.description, monthly_price_cents = excluded.monthly_price_cents, annual_price_cents = excluded.annual_price_cents, analysis_quota = excluded.analysis_quota, max_resumes = excluded.max_resumes, features = excluded.features;

-- Career domains
insert into career_domains (slug, name, description, icon, sort_order) values ('frontend-developer', 'Frontend Developer', 'Interfaces, component architecture and browser performance.', 'layout', 0)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('backend-developer', 'Backend Developer', 'APIs, data modelling, reliability and server-side logic.', 'server', 1)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('full-stack-developer', 'Full-Stack Developer', 'End-to-end product delivery across client and server.', 'layers', 2)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('react-developer', 'React.js Developer', 'Deep React expertise: state, rendering and component design.', 'atom', 3)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('python-developer', 'Python Developer', 'Python services, automation, data pipelines and scripting.', 'code', 4)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('java-developer', 'Java Developer', 'JVM services, enterprise integration and concurrency.', 'coffee', 5)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('software-engineer', 'Software Engineer', 'Generalist engineering: design, build, test, operate.', 'cpu', 6)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('ui-ux-designer', 'UI/UX Designer', 'Research, flows, interface design and design systems.', 'pen-tool', 7)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('graphic-designer', 'Graphic Designer', 'Visual identity, layout and brand communication.', 'palette', 8)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('data-analyst', 'Data Analyst', 'Turn data into decisions: SQL, dashboards and clear reporting.', 'bar-chart', 9)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('data-scientist', 'Data Scientist', 'Modelling, experimentation and production ML.', 'brain', 10)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('cybersecurity-engineer', 'Cybersecurity Engineer', 'Harden systems, test defences and respond to incidents.', 'shield', 11)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('devops-engineer', 'DevOps Engineer', 'Automate build, release and infrastructure with observability.', 'infinity', 12)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('digital-marketer', 'Digital Marketer', 'Acquisition, content and lifecycle marketing with measurable ROI.', 'megaphone', 13)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('business-analyst', 'Business Analyst', 'Translate business needs into testable requirements.', 'clipboard', 14)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;
insert into career_domains (slug, name, description, icon, sort_order) values ('project-manager', 'Project Manager', 'Plan, coordinate and deliver across teams and constraints.', 'calendar', 15)
on conflict (slug) do update set name = excluded.name, description = excluded.description, icon = excluded.icon, sort_order = excluded.sort_order;

-- Skills
insert into skills (canonical_name, aliases, kind, category) values ('HTML5', array['HTML', 'HTML 5'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('CSS3', array['CSS', 'CSS 3'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('JavaScript', array['JS', 'ES6', 'ECMAScript', 'JavaScript ES6'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('TypeScript', array['TS'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('React.js', array['React', 'ReactJS', 'React JS'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Next.js', array['NextJS', 'Next JS'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Vue.js', array['Vue', 'VueJS'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Angular', array['AngularJS'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Redux', array['Redux Toolkit', 'RTK'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Tailwind CSS', array['Tailwind', 'TailwindCSS'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Responsive Design', array['Responsive Web Design', 'Mobile First Design'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Accessibility', array['a11y', 'WCAG'], 'technical'::skill_kind, 'frontend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('REST APIs', array['REST', 'RESTful APIs', 'REST API'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('GraphQL', array['Graph QL', 'Apollo'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Node.js', array['Node', 'NodeJS'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Express.js', array['Express', 'ExpressJS'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Python', array['Python 3'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('FastAPI', array['Fast API'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Django', '{}', 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Flask', '{}', 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Java', array['Java 8', 'Java 17'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Spring Boot', array['Spring'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('C#', array['CSharp', 'C Sharp'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('ASP.NET', array['ASP.NET Core', 'dotnet', '.NET'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('PHP', array['PHP 8'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Laravel', '{}', 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Go', array['Golang'], 'technical'::skill_kind, 'backend')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('SQL', array['Structured Query Language'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('PostgreSQL', array['Postgres', 'psql'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('MySQL', '{}', 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('MongoDB', array['Mongo'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Redis', '{}', 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Database Design', array['Schema Design', 'Normalization', 'Data Modeling'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Pandas', '{}', 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('NumPy', array['Numpy'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Scikit-learn', array['sklearn', 'Scikit Learn'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('TensorFlow', array['TF'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('PyTorch', '{}', 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Machine Learning', array['ML', 'Statistical Learning'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Data Visualization', array['Data Visualisation', 'Dashboards'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Statistics', array['Statistical Analysis', 'Probability'], 'technical'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Excel', array['Microsoft Excel', 'Advanced Excel'], 'tool'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Power BI', array['PowerBI'], 'tool'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Tableau', '{}', 'tool'::skill_kind, 'data')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Git', array['Version Control'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('GitHub', array['Git Hub'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Docker', array['Containerization', 'Containers'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Kubernetes', array['K8s'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('CI/CD', array['Continuous Integration', 'Continuous Delivery', 'GitHub Actions', 'Jenkins'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Linux', array['Ubuntu', 'Unix', 'Bash', 'Shell Scripting'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('AWS', array['Amazon Web Services', 'EC2', 'S3', 'Lambda'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Azure', array['Microsoft Azure'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Google Cloud', array['GCP'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Terraform', array['Infrastructure as Code', 'IaC'], 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Nginx', '{}', 'tool'::skill_kind, 'engineering')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Jest', array['Unit Testing', 'Vitest'], 'tool'::skill_kind, 'testing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Pytest', array['PyTest'], 'tool'::skill_kind, 'testing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Selenium', array['Playwright', 'Cypress', 'End-to-End Testing'], 'tool'::skill_kind, 'testing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Figma', array['Figma Design'], 'tool'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Adobe Photoshop', array['Photoshop'], 'tool'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Adobe Illustrator', array['Illustrator'], 'tool'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Sketch', '{}', 'tool'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('User Research', array['UX Research', 'Usability Testing', 'Interviews'], 'technical'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Wireframing', array['Wireframes', 'Prototyping', 'Prototypes'], 'technical'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Design Systems', array['Component Library', 'UI Kit'], 'technical'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Typography', array['Type Hierarchy'], 'technical'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Brand Identity', array['Branding', 'Logo Design'], 'technical'::skill_kind, 'design')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Penetration Testing', array['Pen Testing', 'Ethical Hacking', 'Pentesting'], 'technical'::skill_kind, 'security')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Network Security', array['Firewalls', 'IDS', 'IPS'], 'technical'::skill_kind, 'security')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('OWASP', array['OWASP Top 10', 'Web Application Security'], 'technical'::skill_kind, 'security')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Cryptography', array['Encryption', 'TLS'], 'technical'::skill_kind, 'security')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Incident Response', array['Forensics', 'SIEM'], 'technical'::skill_kind, 'security')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('SEO', array['Search Engine Optimization', 'On-page SEO'], 'technical'::skill_kind, 'marketing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Google Analytics', array['GA4', 'Web Analytics'], 'tool'::skill_kind, 'marketing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Content Marketing', array['Copywriting', 'Content Strategy'], 'technical'::skill_kind, 'marketing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Email Marketing', array['Mailchimp', 'Campaigns'], 'technical'::skill_kind, 'marketing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Paid Advertising', array['Google Ads', 'Meta Ads', 'PPC'], 'technical'::skill_kind, 'marketing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Social Media Marketing', array['SMM', 'Social Media'], 'technical'::skill_kind, 'marketing')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Market Research', array['Competitive Analysis'], 'technical'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Business Process Modeling', array['BPMN', 'Process Mapping'], 'technical'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Requirements Gathering', array['Elicitation', 'BRD', 'User Stories'], 'technical'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Stakeholder Management', array['Stakeholder Communication'], 'soft'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Agile', array['Scrum', 'Kanban', 'Sprint Planning'], 'technical'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Jira', array['Atlassian Jira'], 'tool'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Project Planning', array['Roadmapping', 'Gantt', 'Timeline Planning'], 'technical'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Risk Management', array['Risk Assessment'], 'technical'::skill_kind, 'business')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Communication', array['Written Communication', 'Verbal Communication'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Teamwork', array['Collaboration', 'Cross-functional Collaboration'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Problem Solving', array['Analytical Thinking', 'Critical Thinking'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Leadership', array['Team Leadership', 'Mentoring'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Time Management', array['Prioritization', 'Deadline Management'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Adaptability', array['Flexibility'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Attention to Detail', array['Detail Oriented'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;
insert into skills (canonical_name, aliases, kind, category) values ('Presentation Skills', array['Public Speaking', 'Demoing'], 'soft'::skill_kind, 'interpersonal')
on conflict (canonical_name) do update set aliases = excluded.aliases, kind = excluded.kind, category = excluded.category;

-- Domain skill mapping
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'HTML5'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'CSS3'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'JavaScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'React.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Responsive Design'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'REST APIs'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'TypeScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Redux'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Tailwind CSS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Accessibility'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Jest'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Next.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Figma'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Design Systems'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'frontend-developer' and s.canonical_name = 'Vue.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'REST APIs'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Database Design'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Python'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Node.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'PostgreSQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Redis'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'FastAPI'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Express.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Linux'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'GraphQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'Kubernetes'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'backend-developer' and s.canonical_name = 'CI/CD'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'JavaScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'React.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'REST APIs'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'HTML5'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'CSS3'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'TypeScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'Node.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'PostgreSQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'Database Design'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'Next.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'CI/CD'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'full-stack-developer' and s.canonical_name = 'Redis'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'HTML5'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'CSS3'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'JavaScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'React.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'TypeScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Redux'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'REST APIs'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Responsive Design'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Jest'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Tailwind CSS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Accessibility'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Next.js'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'GraphQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Design Systems'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'react-developer' and s.canonical_name = 'Figma'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Python'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'REST APIs'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'FastAPI'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Django'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Pandas'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'PostgreSQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Linux'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Redis'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'Pytest'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'python-developer' and s.canonical_name = 'NumPy'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Java'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'REST APIs'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Spring Boot'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'PostgreSQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'CI/CD'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Database Design'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Kubernetes'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Redis'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'java-developer' and s.canonical_name = 'Agile'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'REST APIs'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Problem Solving'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Python'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'JavaScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Database Design'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'CI/CD'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Agile'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Kubernetes'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'Redis'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'software-engineer' and s.canonical_name = 'TypeScript'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Figma'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'User Research'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Wireframing'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Design Systems'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Accessibility'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Typography'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'HTML5'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'CSS3'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Adobe Illustrator'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Adobe Photoshop'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'ui-ux-designer' and s.canonical_name = 'Sketch'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Adobe Photoshop'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Adobe Illustrator'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Typography'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Brand Identity'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Figma'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Design Systems'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Attention to Detail'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Adobe Photoshop'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Social Media Marketing'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'graphic-designer' and s.canonical_name = 'Market Research'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Excel'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Data Visualization'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Statistics'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Python'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Power BI'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Tableau'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Pandas'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Database Design'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Machine Learning'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Google Analytics'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'data-analyst' and s.canonical_name = 'Market Research'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Python'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Statistics'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Machine Learning'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Pandas'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Scikit-learn'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'NumPy'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Data Visualization'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'TensorFlow'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'PyTorch'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'data-scientist' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Network Security'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'OWASP'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Linux'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Penetration Testing'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Cryptography'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Incident Response'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Python'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Kubernetes'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'CI/CD'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'cybersecurity-engineer' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Linux'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Docker'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'CI/CD'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Git'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'AWS'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Kubernetes'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Terraform'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Python'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Nginx'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Redis'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'PostgreSQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Network Security'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'devops-engineer' and s.canonical_name = 'Incident Response'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'SEO'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Google Analytics'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Content Marketing'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Social Media Marketing'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Email Marketing'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Paid Advertising'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Market Research'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Adobe Photoshop'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Data Visualization'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'digital-marketer' and s.canonical_name = 'Excel'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Requirements Gathering'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Business Process Modeling'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Stakeholder Management'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Agile'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Jira'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Excel'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Data Visualization'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Power BI'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Project Planning'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'business-analyst' and s.canonical_name = 'Market Research'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Project Planning'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Stakeholder Management'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Risk Management'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Agile'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'required'::requirement_level, 3.0
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Communication'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Jira'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Time Management'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Leadership'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'preferred'::requirement_level, 1.5
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Excel'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'SQL'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Business Process Modeling'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;
insert into domain_skills (domain_id, skill_id, requirement, weight)
select d.id, s.id, 'optional'::requirement_level, 0.5
from career_domains d, skills s where d.slug = 'project-manager' and s.canonical_name = 'Data Visualization'
on conflict (domain_id, skill_id) do update set requirement = excluded.requirement, weight = excluded.weight;

-- Templates
insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ('ats-friendly', 'ATS-Friendly', 'Single column, standard headings, no graphics. Maximum parser compatibility.', 'free'::template_tier, true, '{"columns": 1, "accent": "#1e293b", "font": "Inter", "show_photo": false, "section_order": ["summary", "skills", "experience", "education", "projects", "certifications"]}'::jsonb, 0)
on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;
insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ('modern-professional', 'Modern Professional', 'Two-column header with a subtle accent rule. Balanced for corporate roles.', 'pro'::template_tier, true, '{"columns": 1, "accent": "#4338ca", "font": "Inter", "show_photo": false, "section_order": ["summary", "experience", "skills", "education", "projects", "certifications"]}'::jsonb, 1)
on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;
insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ('software-developer', 'Software Developer', 'Technical skills grid above experience, project-first for engineers.', 'pro'::template_tier, true, '{"columns": 1, "accent": "#0f766e", "font": "JetBrains Mono", "show_photo": false, "section_order": ["summary", "skills", "projects", "experience", "education", "certifications"]}'::jsonb, 2)
on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;
insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ('fresh-graduate', 'Fresh Graduate', 'Education and coursework lead, projects carry the weight.', 'pro'::template_tier, true, '{"columns": 1, "accent": "#2563eb", "font": "Inter", "show_photo": false, "section_order": ["summary", "education", "projects", "skills", "experience", "achievements"]}'::jsonb, 3)
on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;
insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ('experienced-professional', 'Experienced Professional', 'Achievement-dense experience section for 5+ years.', 'premium'::template_tier, true, '{"columns": 1, "accent": "#334155", "font": "Source Serif", "show_photo": false, "section_order": ["summary", "experience", "achievements", "skills", "education", "certifications"]}'::jsonb, 4)
on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;
insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ('creative-designer', 'Creative Designer', 'Asymmetric header, strong type hierarchy, still single column body.', 'premium'::template_tier, false, '{"columns": 1, "accent": "#be185d", "font": "Playfair Display", "show_photo": true, "section_order": ["summary", "skills", "projects", "experience", "education", "achievements"]}'::jsonb, 5)
on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;
insert into resume_templates (slug, name, description, tier, is_ats_safe, layout, sort_order) values ('minimalist', 'Minimalist', 'Quiet typography, generous whitespace, no rules or boxes.', 'free'::template_tier, true, '{"columns": 1, "accent": "#111827", "font": "Inter", "show_photo": false, "section_order": ["summary", "experience", "education", "skills", "projects"]}'::jsonb, 6)
on conflict (slug) do update set name = excluded.name, description = excluded.description, tier = excluded.tier, is_ats_safe = excluded.is_ats_safe, layout = excluded.layout, sort_order = excluded.sort_order;

-- Default scoring weights (admin-editable)
insert into app_settings (key, value)
values ('scoring_weights', '{"keyword_match": 20, "technical_skills": 20, "ats_compatibility": 15, "content_quality": 15, "grammar": 10, "formatting": 10, "experience_relevance": 10}'::jsonb)
on conflict (key) do nothing;

