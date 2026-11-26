import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, LogOut, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { PageHeader } from "@/components/shared";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Select } from "@/components/ui/field";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { accountApi } from "@/services/account";
import { catalogApi } from "@/services/catalog";

export function SettingsPage() {
  const { me, refreshMe, signOut } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [fullName, setFullName] = useState("");
  const [headline, setHeadline] = useState("");
  const [domainId, setDomainId] = useState("");
  const [confirmDelete, setConfirmDelete] = useState("");

  useEffect(() => {
    if (me) {
      setFullName(me.profile.full_name ?? "");
      setHeadline(me.profile.headline ?? "");
      setDomainId(me.profile.career_domain_id ?? "");
    }
  }, [me]);

  const domainsQuery = useQuery({ queryKey: ["domains"], queryFn: catalogApi.domains });

  const save = useMutation({
    mutationFn: () =>
      accountApi.updateProfile({
        full_name: fullName,
        headline,
        career_domain_id: domainId || null,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      await refreshMe();
      toast.push("Profile updated", "success");
    },
    onError: (error) => toast.push(error instanceof ApiError ? error.message : "Could not save", "error"),
  });

  const exportData = useMutation({
    mutationFn: accountApi.exportData,
    onSuccess: ({ url }) => {
      window.open(url, "_blank", "noopener");
      toast.push("Export ready. The link expires in 5 minutes.", "success");
    },
    onError: (error) => toast.push(error instanceof ApiError ? error.message : "Export failed", "error"),
  });

  const deleteAccount = useMutation({
    mutationFn: accountApi.deleteAccount,
    onSuccess: async () => {
      await signOut();
      navigate("/", { replace: true });
    },
    onError: (error) => toast.push(error instanceof ApiError ? error.message : "Could not delete the account", "error"),
  });

  return (
    <div>
      <PageHeader eyebrow="Settings" title="Account settings" description="Your profile, default domain and data controls." />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Profile</CardTitle></CardHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" value={me?.profile.email ?? ""} disabled />
            </div>
            <div>
              <Label htmlFor="fullName">Full name</Label>
              <Input id="fullName" value={fullName} onChange={(event) => setFullName(event.target.value)} maxLength={120} />
            </div>
            <div>
              <Label htmlFor="headline">Headline</Label>
              <Input id="headline" value={headline} onChange={(event) => setHeadline(event.target.value)} placeholder="Frontend Developer" maxLength={160} />
            </div>
            <div>
              <Label htmlFor="domain">Default career domain</Label>
              <Select id="domain" value={domainId} onChange={(event) => setDomainId(event.target.value)}>
                <option value="">Not set</option>
                {domainsQuery.data?.map((domain) => (
                  <option key={domain.id} value={domain.id}>{domain.name}</option>
                ))}
              </Select>
            </div>
            <Button onClick={() => save.mutate()} loading={save.isPending}>Save changes</Button>
          </div>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Your data</CardTitle></CardHeader>
            <p className="text-sm leading-relaxed text-slate-600">
              Export a JSON bundle of your profile, resumes metadata and analyses. Documents stay in private storage
              and are downloadable individually.
            </p>
            <Button variant="outline" className="mt-3" onClick={() => exportData.mutate()} loading={exportData.isPending}>
              <Download className="h-4 w-4" /> Request export
            </Button>
          </Card>

          <Card>
            <CardHeader><CardTitle>Session</CardTitle></CardHeader>
            <p className="text-sm text-slate-600">Sign out of this browser. Other devices keep their sessions.</p>
            <Button
              variant="outline"
              className="mt-3"
              onClick={async () => {
                await signOut();
                navigate("/login", { replace: true });
              }}
            >
              <LogOut className="h-4 w-4" /> Sign out
            </Button>
          </Card>

          <Card className="border-rose-200">
            <CardHeader><CardTitle className="text-rose-700">Delete account</CardTitle></CardHeader>
            <Alert tone="danger">
              This deletes your resumes, analyses and account. It cannot be undone. Payment records are retained for
              accounting as required by law.
            </Alert>
            <div className="mt-3">
              <Label htmlFor="confirm">Type DELETE to confirm</Label>
              <Input id="confirm" value={confirmDelete} onChange={(event) => setConfirmDelete(event.target.value)} />
              <Button
                variant="danger"
                className="mt-3"
                disabled={confirmDelete !== "DELETE"}
                loading={deleteAccount.isPending}
                onClick={() => deleteAccount.mutate()}
              >
                <Trash2 className="h-4 w-4" /> Delete my account
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
