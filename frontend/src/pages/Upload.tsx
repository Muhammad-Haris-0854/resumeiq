import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, FileText, Loader2, UploadCloud } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { PageHeader } from "@/components/shared";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input, Label, Select } from "@/components/ui/field";
import { Progress } from "@/components/ui/progress";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { cn, formatBytes } from "@/lib/utils";
import { analysesApi } from "@/services/analyses";
import { catalogApi } from "@/services/catalog";
import { resumesApi } from "@/services/resumes";

const MAX_BYTES = 5 * 1024 * 1024;
type Stage = "idle" | "uploading" | "extracting" | "analysing" | "done";

export function UploadPage() {
  const { me } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();
  const inputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [domainId, setDomainId] = useState(me?.profile.career_domain_id ?? "");
  const [stage, setStage] = useState<Stage>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const domainsQuery = useQuery({ queryKey: ["domains"], queryFn: catalogApi.domains });

  useEffect(() => {
    if (!domainId && domainsQuery.data?.length) {
      setDomainId(me?.profile.career_domain_id ?? domainsQuery.data[0]!.id);
    }
  }, [domainsQuery.data, domainId, me?.profile.career_domain_id]);

  const pickFile = useCallback((picked: File | null) => {
    setError(null);
    if (!picked) return;
    const validType = /\.(pdf|docx)$/i.test(picked.name);
    if (!validType) {
      setError("Upload a PDF or DOCX file.");
      return;
    }
    if (picked.size > MAX_BYTES) {
      setError("That file is larger than 5 MB.");
      return;
    }
    setFile(picked);
    if (!title) setTitle(picked.name.replace(/\.(pdf|docx)$/i, ""));
  }, [title]);

  const upload = useMutation({
    mutationFn: async () => {
      if (!file || !domainId) throw new ApiError("Pick a file and a career domain first.");
      setStage("uploading");
      setProgress(25);
      const resume = await resumesApi.upload(file, title || file.name, domainId);
      setProgress(45);

      setStage("extracting");
      let versionId: string | null = null;
      for (let attempt = 0; attempt < 30; attempt += 1) {
        const detail = await resumesApi.get(resume.id);
        const current = detail.versions.find((version) => version.id === detail.current_version_id) ?? detail.versions[0];
        if (detail.status === "extracted" && current) {
          versionId = current.id;
          break;
        }
        if (detail.status === "failed") throw new ApiError("We could not read this document. Try a text-based PDF.");
        await new Promise((resolve) => setTimeout(resolve, 1500));
      }
      if (!versionId) throw new ApiError("Extraction is taking longer than expected. Check the resume list in a minute.");

      setStage("analysing");
      setProgress(75);
      const analysis = await analysesApi.create({
        resume_version_id: versionId,
        career_domain_id: domainId,
      });
      setProgress(100);
      setStage("done");
      return analysis;
    },
    onSuccess: async (analysis) => {
      await queryClient.invalidateQueries({ queryKey: ["analyses"] });
      await queryClient.invalidateQueries({ queryKey: ["resumes"] });
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      toast.push("Analysis queued. This takes a few seconds.", "success");
      navigate(`/analyses/${analysis.id}`);
    },
    onError: (err) => {
      setStage("idle");
      setProgress(0);
      setError(err instanceof ApiError ? err.message : "Upload failed. Try again.");
    },
  });

  const busy = upload.isPending;
  const steps = [
    { key: "uploading", label: "Uploading to private storage" },
    { key: "extracting", label: "Extracting text and sections" },
    { key: "analysing", label: "Scoring against the domain" },
  ];
  const stageIndex = steps.findIndex((step) => step.key === stage);

  return (
    <div>
      <PageHeader
        eyebrow="New analysis"
        title="Upload your resume"
        description="PDF or DOCX, up to 5 MB. Scanned PDFs are read with OCR."
      />

      <div className="grid gap-4 lg:grid-cols-[1.3fr_1fr]">
        <div className="surface p-5">
          <div
            role="button"
            tabIndex={0}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") inputRef.current?.click();
            }}
            onDragOver={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragging(false);
              pickFile(event.dataTransfer.files[0] ?? null);
            }}
            className={cn(
              "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-12 text-center transition-colors",
              dragging ? "border-brand-500 bg-brand-50" : "border-line bg-canvas hover:border-slate-300",
            )}
          >
            <span className="rounded-2xl bg-white p-3 text-brand-600 shadow-sm">
              <UploadCloud className="h-6 w-6" aria-hidden />
            </span>
            {file ? (
              <>
                <p className="text-sm font-semibold text-ink">{file.name}</p>
                <p className="text-xs text-slate-500">{formatBytes(file.size)} · ready to analyse</p>
              </>
            ) : (
              <>
                <p className="text-sm font-semibold text-ink">Drop your resume here, or click to browse</p>
                <p className="text-xs text-slate-500">PDF or DOCX · max 5 MB</p>
              </>
            )}
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="hidden"
              onChange={(event) => pickFile(event.target.files?.[0] ?? null)}
            />
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="title">Resume name</Label>
              <Input
                id="title"
                value={title}
                placeholder="Frontend resume v3"
                onChange={(event) => setTitle(event.target.value)}
                maxLength={120}
              />
            </div>
            <div>
              <Label htmlFor="domain">Career domain</Label>
              <Select id="domain" value={domainId} onChange={(event) => setDomainId(event.target.value)}>
                <option value="">Select a domain</option>
                {domainsQuery.data?.map((domain) => (
                  <option key={domain.id} value={domain.id}>
                    {domain.name}
                  </option>
                ))}
              </Select>
            </div>
          </div>

          {error && <Alert tone="danger" className="mt-4">{error}</Alert>}

          <div className="mt-5 flex items-center gap-3">
            <Button onClick={() => upload.mutate()} loading={busy} disabled={!file || !domainId}>
              <FileText className="h-4 w-4" /> Analyse resume
            </Button>
            <p className="text-xs text-slate-500">
              {me ? `${me.entitlements.analyses_remaining} analyses left this month` : ""}
            </p>
          </div>
        </div>

        <div className="surface h-fit p-5">
          <p className="label">Progress</p>
          <div className="mt-3 space-y-3">
            {steps.map((step, index) => {
              const complete = stageIndex > index || stage === "done";
              const active = stageIndex === index;
              return (
                <div key={step.key} className="flex items-center gap-3">
                  <span
                    className={cn(
                      "grid h-7 w-7 place-items-center rounded-full text-xs font-semibold",
                      complete ? "bg-emerald-100 text-emerald-700" : active ? "bg-brand-100 text-brand-700" : "bg-slate-100 text-slate-400",
                    )}
                  >
                    {complete ? <CheckCircle2 className="h-4 w-4" /> : active ? <Loader2 className="h-4 w-4 animate-spin" /> : index + 1}
                  </span>
                  <span className={cn("text-sm", active || complete ? "text-ink" : "text-slate-500")}>{step.label}</span>
                </div>
              );
            })}
          </div>
          <Progress value={progress} className="mt-4" />
          <div className="mt-5 rounded-xl bg-canvas p-3 text-xs leading-relaxed text-slate-600">
            <p className="font-semibold text-ink">What we extract</p>
            <p className="mt-1">
              Contact details, summary, skills, experience with bullets, education, projects, certifications and
              languages. The original file stays private; only you can download it.
            </p>
          </div>
          {stage === "done" && <Badge tone="success" className="mt-4">Redirecting to your report…</Badge>}
        </div>
      </div>
    </div>
  );
}
