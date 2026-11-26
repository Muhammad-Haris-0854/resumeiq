import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowLeft, ArrowUp, Download, Plus, Save, Trash2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState, Loading, PageHeader } from "@/components/shared";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Textarea } from "@/components/ui/field";
import { Tabs } from "@/components/ui/tabs";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { previewHtml } from "@/lib/preview";
import { cn } from "@/lib/utils";
import { builderApi } from "@/services/builder";
import type { ResumeContent } from "@/types";

const SECTION_LABELS: Record<string, string> = {
  summary: "Summary",
  skills: "Skills",
  experience: "Experience",
  education: "Education",
  projects: "Projects",
  certifications: "Certifications",
  achievements: "Achievements",
  languages: "Languages",
};

function emptyContent(): ResumeContent {
  return {
    full_name: "",
    headline: "",
    email: "",
    phone: "",
    location: "",
    links: [],
    summary: "",
    skills: [],
    experience: [],
    education: [],
    projects: [],
    certifications: [],
    achievements: [],
    languages: [],
    custom_sections: {},
    section_order: ["summary", "skills", "experience", "education", "projects"],
  };
}

export function EditorPage() {
  const { generatedId } = useParams<{ generatedId: string }>();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [content, setContent] = useState<ResumeContent | null>(null);
  const [tab, setTab] = useState("content");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">("idle");
  const initialised = useRef(false);

  const resumeQuery = useQuery({
    queryKey: ["generated-resume", generatedId],
    queryFn: () => builderApi.get(generatedId!),
    enabled: Boolean(generatedId),
  });
  const templatesQuery = useQuery({ queryKey: ["templates"], queryFn: builderApi.templates });

  useEffect(() => {
    if (resumeQuery.data && !initialised.current) {
      setContent({ ...emptyContent(), ...resumeQuery.data.content });
      initialised.current = true;
    }
  }, [resumeQuery.data]);

  const template = templatesQuery.data?.find((item) => item.id === resumeQuery.data?.template_id);
  const accent = String((template?.layout as { accent?: string } | undefined)?.accent ?? "#1e293b");
  const font = String((template?.layout as { font?: string } | undefined)?.font ?? "Inter");

  const saveMutation = useMutation({
    mutationFn: (payload: ResumeContent) => builderApi.save(generatedId!, payload),
    onMutate: () => setSaveState("saving"),
    onSuccess: (saved) => {
      setSaveState("saved");
      queryClient.setQueryData(["generated-resume", generatedId], saved);
    },
    onError: (error) => {
      setSaveState("idle");
      toast.push(error instanceof ApiError ? error.message : "Autosave failed", "error");
    },
  });

  useEffect(() => {
    if (!content || !initialised.current) return;
    const timer = window.setTimeout(() => {
      saveMutation.mutate(content);
    }, 1200);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content]);

  const exportMutation = useMutation({
    mutationFn: () => builderApi.export(generatedId!),
    onSuccess: () => toast.push("Export started. The PDF appears in a moment.", "success"),
    onError: (error) => toast.push(error instanceof ApiError ? error.message : "Export failed", "error"),
  });

  const exportPoll = useQuery({
    queryKey: ["generated-resume", generatedId, "pdf"],
    queryFn: () => builderApi.get(generatedId!),
    enabled: Boolean(exportMutation.data),
    refetchInterval: (query) => (query.state.data?.pdf_url ? false : 2500),
  });

  useEffect(() => {
    if (exportPoll.data?.pdf_url) {
      window.open(exportPoll.data.pdf_url, "_blank", "noopener");
    }
  }, [exportPoll.data?.pdf_url]);

  const preview = useMemo(() => (content ? previewHtml(content, accent, font) : ""), [content, accent, font]);

  if (resumeQuery.isLoading || !content) return <Loading label="Loading editor" />;
  if (resumeQuery.isError) return <ErrorState error={resumeQuery.error as Error} onRetry={() => void resumeQuery.refetch()} />;

  const update = <K extends keyof ResumeContent>(key: K, value: ResumeContent[K]) => {
    setContent((current) => (current ? { ...current, [key]: value } : current));
  };

  const moveSection = (index: number, direction: -1 | 1) => {
    const order = [...content.section_order];
    const target = index + direction;
    if (target < 0 || target >= order.length) return;
    const [item] = order.splice(index, 1);
    if (item) order.splice(target, 0, item);
    update("section_order", order);
  };

  return (
    <div>
      <div className="mb-4">
        <Link to="/builder" className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-ink">
          <ArrowLeft className="h-3.5 w-3.5" /> All builder resumes
        </Link>
      </div>

      <PageHeader
        eyebrow={`Template: ${template?.name ?? "—"}`}
        title={resumeQuery.data?.title ?? "Resume"}
        description="Every change autosaves and creates a version you can restore."
        actions={
          <>
            <Badge tone={saveState === "saving" ? "info" : saveState === "saved" ? "success" : "neutral"}>
              {saveState === "saving" ? "Saving…" : saveState === "saved" ? "Saved" : "Up to date"}
            </Badge>
            <Button
              variant="outline"
              onClick={() => saveMutation.mutate(content)}
              loading={saveMutation.isPending}
            >
              <Save className="h-4 w-4" /> Save now
            </Button>
            <Button onClick={() => exportMutation.mutate()} loading={exportMutation.isPending}>
              <Download className="h-4 w-4" /> Export PDF
            </Button>
          </>
        }
      />

      {exportMutation.data && !exportPoll.data?.pdf_url && (
        <Alert tone="info" className="mb-4">Rendering your PDF. It opens automatically when ready.</Alert>
      )}

      <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="space-y-4">
          <Tabs
            value={tab}
            onChange={setTab}
            items={[
              { id: "content", label: "Content" },
              { id: "layout", label: "Sections" },
            ]}
          />

          {tab === "content" && (
            <>
              <Card>
                <CardHeader><CardTitle>Header</CardTitle></CardHeader>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <Label htmlFor="full_name">Full name</Label>
                    <Input id="full_name" value={content.full_name} onChange={(e) => update("full_name", e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="headline">Headline</Label>
                    <Input id="headline" value={content.headline} onChange={(e) => update("headline", e.target.value)} placeholder="Frontend Developer" />
                  </div>
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" type="email" value={content.email} onChange={(e) => update("email", e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="phone">Phone</Label>
                    <Input id="phone" value={content.phone} onChange={(e) => update("phone", e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="location">Location</Label>
                    <Input id="location" value={content.location} onChange={(e) => update("location", e.target.value)} placeholder="Karachi, Pakistan" />
                  </div>
                  <div>
                    <Label htmlFor="links">Links (one per line)</Label>
                    <Textarea
                      id="links"
                      rows={2}
                      value={content.links.join("\n")}
                      onChange={(e) => update("links", e.target.value.split("\n").filter(Boolean))}
                    />
                  </div>
                </div>
              </Card>

              <Card>
                <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
                <Textarea rows={4} value={content.summary} onChange={(e) => update("summary", e.target.value)} maxLength={1200} />
                <p className="mt-1 text-xs text-slate-500">{content.summary.length}/1200</p>
              </Card>

              <Card>
                <CardHeader><CardTitle>Skills</CardTitle></CardHeader>
                <Textarea
                  rows={3}
                  value={content.skills.join(", ")}
                  onChange={(e) => update("skills", e.target.value.split(",").map((s) => s.trim()).filter(Boolean))}
                  placeholder="React, TypeScript, Redux"
                />
                <p className="mt-1 text-xs text-slate-500">Comma separated. These are the terms an ATS will match.</p>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Experience</CardTitle>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      update("experience", [
                        ...content.experience,
                        { title: "", company: "", location: "", start_date: "", end_date: "", bullets: [""] },
                      ])
                    }
                  >
                    <Plus className="h-3.5 w-3.5" /> Add role
                  </Button>
                </CardHeader>
                <div className="space-y-4">
                  {content.experience.map((role, index) => (
                    <div key={index} className="rounded-xl border border-line p-3">
                      <div className="grid gap-2 sm:grid-cols-2">
                        <Input
                          placeholder="Job title"
                          value={role.title}
                          onChange={(e) => {
                            const next = [...content.experience];
                            next[index] = { ...role, title: e.target.value };
                            update("experience", next);
                          }}
                        />
                        <Input
                          placeholder="Company"
                          value={role.company}
                          onChange={(e) => {
                            const next = [...content.experience];
                            next[index] = { ...role, company: e.target.value };
                            update("experience", next);
                          }}
                        />
                        <Input
                          placeholder="Start (Jan 2023)"
                          value={role.start_date}
                          onChange={(e) => {
                            const next = [...content.experience];
                            next[index] = { ...role, start_date: e.target.value };
                            update("experience", next);
                          }}
                        />
                        <Input
                          placeholder="End (Present)"
                          value={role.end_date}
                          onChange={(e) => {
                            const next = [...content.experience];
                            next[index] = { ...role, end_date: e.target.value };
                            update("experience", next);
                          }}
                        />
                      </div>
                      <div className="mt-2">
                        <Label>Bullets (one per line)</Label>
                        <Textarea
                          rows={4}
                          value={role.bullets.join("\n")}
                          onChange={(e) => {
                            const next = [...content.experience];
                            next[index] = { ...role, bullets: e.target.value.split("\n") };
                            update("experience", next);
                          }}
                        />
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="mt-2 text-rose-600"
                        onClick={() => update("experience", content.experience.filter((_, i) => i !== index))}
                      >
                        <Trash2 className="h-3.5 w-3.5" /> Remove role
                      </Button>
                    </div>
                  ))}
                  {content.experience.length === 0 && <p className="text-sm text-slate-500">No roles yet.</p>}
                </div>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Education</CardTitle>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      update("education", [
                        ...content.education,
                        { degree: "", institution: "", location: "", start_date: "", end_date: "", details: "" },
                      ])
                    }
                  >
                    <Plus className="h-3.5 w-3.5" /> Add education
                  </Button>
                </CardHeader>
                <div className="space-y-3">
                  {content.education.map((item, index) => (
                    <div key={index} className="grid gap-2 rounded-xl border border-line p-3 sm:grid-cols-2">
                      <Input
                        placeholder="Degree"
                        value={item.degree}
                        onChange={(e) => {
                          const next = [...content.education];
                          next[index] = { ...item, degree: e.target.value };
                          update("education", next);
                        }}
                      />
                      <Input
                        placeholder="Institution"
                        value={item.institution}
                        onChange={(e) => {
                          const next = [...content.education];
                          next[index] = { ...item, institution: e.target.value };
                          update("education", next);
                        }}
                      />
                      <Input
                        placeholder="Start"
                        value={item.start_date}
                        onChange={(e) => {
                          const next = [...content.education];
                          next[index] = { ...item, start_date: e.target.value };
                          update("education", next);
                        }}
                      />
                      <Input
                        placeholder="End"
                        value={item.end_date}
                        onChange={(e) => {
                          const next = [...content.education];
                          next[index] = { ...item, end_date: e.target.value };
                          update("education", next);
                        }}
                      />
                      <div className="sm:col-span-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-rose-600"
                          onClick={() => update("education", content.education.filter((_, i) => i !== index))}
                        >
                          <Trash2 className="h-3.5 w-3.5" /> Remove
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              <Card>
                <CardHeader><CardTitle>Certifications, achievements, languages</CardTitle></CardHeader>
                <div className="grid gap-3 sm:grid-cols-3">
                  <div>
                    <Label>Certifications</Label>
                    <Textarea
                      rows={3}
                      value={content.certifications.join("\n")}
                      onChange={(e) => update("certifications", e.target.value.split("\n").filter(Boolean))}
                    />
                  </div>
                  <div>
                    <Label>Achievements</Label>
                    <Textarea
                      rows={3}
                      value={content.achievements.join("\n")}
                      onChange={(e) => update("achievements", e.target.value.split("\n").filter(Boolean))}
                    />
                  </div>
                  <div>
                    <Label>Languages</Label>
                    <Textarea
                      rows={3}
                      value={content.languages.join("\n")}
                      onChange={(e) => update("languages", e.target.value.split("\n").filter(Boolean))}
                    />
                  </div>
                </div>
              </Card>
            </>
          )}

          {tab === "layout" && (
            <Card>
              <CardHeader><CardTitle>Section order</CardTitle></CardHeader>
              <ul className="space-y-2">
                {content.section_order.map((section, index) => (
                  <li key={section} className="flex items-center justify-between rounded-xl border border-line px-3 py-2">
                    <span className="text-sm font-medium text-ink">{SECTION_LABELS[section] ?? section}</span>
                    <div className="flex gap-1">
                      <Button size="icon" variant="ghost" aria-label="Move up" onClick={() => moveSection(index, -1)}>
                        <ArrowUp className="h-4 w-4" />
                      </Button>
                      <Button size="icon" variant="ghost" aria-label="Move down" onClick={() => moveSection(index, 1)}>
                        <ArrowDown className="h-4 w-4" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        aria-label="Remove section"
                        onClick={() => update("section_order", content.section_order.filter((item) => item !== section))}
                      >
                        <Trash2 className="h-4 w-4 text-rose-500" />
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
              <div className="mt-4 flex flex-wrap gap-2">
                {Object.keys(SECTION_LABELS)
                  .filter((section) => !content.section_order.includes(section))
                  .map((section) => (
                    <Button
                      key={section}
                      size="sm"
                      variant="outline"
                      onClick={() => update("section_order", [...content.section_order, section])}
                    >
                      <Plus className="h-3.5 w-3.5" /> {SECTION_LABELS[section]}
                    </Button>
                  ))}
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="label">Live preview</p>
            <Badge tone="neutral">A4 · ATS safe</Badge>
          </div>
          <div className={cn("overflow-hidden rounded-2xl border border-line bg-white shadow-card")}>
            <iframe
              title="Resume preview"
              srcDoc={preview}
              className="h-[820px] w-full"
              sandbox=""
            />
          </div>
        </div>
      </div>
    </div>
  );
}
