from __future__ import annotations

import fitz

from app.services.normalizer import normalise
from tests.conftest import DOM_REACT, RESUME_TEXT, TPL_ATS, TPL_PREMIUM


def _pdf() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((56, 72), RESUME_TEXT[:1500], fontsize=9)
    data = document.tobytes()
    document.close()
    return data


def _upload(client, name="resume.pdf"):
    return client.post(
        "/v1/resumes",
        files={"file": (name, _pdf(), "application/pdf")},
        data={"title": "Frontend resume", "career_domain_id": DOM_REACT},
    )


def test_me_returns_profile_and_entitlements(client):
    response = client.get("/v1/me")
    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["plan"] == "free"
    assert body["entitlements"]["analysis_quota"] == 2
    assert body["entitlements"]["analyses_remaining"] == 2


def test_upload_rejects_non_pdf(client):
    response = client.post(
        "/v1/resumes", files={"file": ("resume.txt", b"just text", "text/plain")}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "UNSUPPORTED_FORMAT"


def test_upload_creates_resume_and_version(client, repos):
    response = _upload(client)
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["status"] == "uploaded"
    versions = repos.resumes.list_versions(body["id"])
    assert len(versions) == 1
    assert ("resumes", versions[0]["storage_path"]) in repos.storage.objects


def test_resume_list_and_detail(client):
    resume_id = _upload(client).json()["id"]
    listing = client.get("/v1/resumes").json()
    assert listing["total"] == 1
    detail = client.get(f"/v1/resumes/{resume_id}").json()
    assert len(detail["versions"]) == 1


def test_download_returns_signed_url(client):
    resume_id = _upload(client).json()["id"]
    response = client.get(f"/v1/resumes/{resume_id}/download")
    assert response.status_code == 200
    assert response.json()["url"].startswith("https://storage.test/resumes/")


def test_analysis_requires_extracted_text(client):
    resume_id = _upload(client).json()["id"]
    version_id = client.get(f"/v1/resumes/{resume_id}").json()["versions"][0]["id"]
    response = client.post(
        "/v1/analyses",
        json={"resume_version_id": version_id, "career_domain_id": DOM_REACT},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "EXTRACTION_PENDING"


def test_analysis_quota_is_enforced(client, repos):
    resume_id = _upload(client).json()["id"]
    version_id = client.get(f"/v1/resumes/{resume_id}").json()["versions"][0]["id"]
    repos.resumes.versions[version_id]["extracted"] = normalise(RESUME_TEXT)
    repos.resumes.versions[version_id]["raw_text"] = RESUME_TEXT

    payload = {"resume_version_id": version_id, "career_domain_id": DOM_REACT}
    first = client.post("/v1/analyses", json=payload)
    second = client.post("/v1/analyses", json=payload)
    third = client.post("/v1/analyses", json=payload)
    assert first.status_code == 202
    assert second.status_code == 202
    assert third.status_code == 429
    assert third.json()["error"]["code"] == "QUOTA_EXCEEDED"


def test_analysis_detail_is_scoped_to_owner(client, repos):
    resume_id = _upload(client).json()["id"]
    version_id = client.get(f"/v1/resumes/{resume_id}").json()["versions"][0]["id"]
    repos.resumes.versions[version_id]["extracted"] = normalise(RESUME_TEXT)
    repos.resumes.versions[version_id]["raw_text"] = RESUME_TEXT
    analysis_id = client.post(
        "/v1/analyses", json={"resume_version_id": version_id, "career_domain_id": DOM_REACT}
    ).json()["id"]

    assert client.get(f"/v1/analyses/{analysis_id}").status_code == 200

    repos.analyses.rows[analysis_id]["user_id"] = "someone-else"
    assert client.get(f"/v1/analyses/{analysis_id}").status_code == 404


def test_unknown_domain_is_rejected(client):
    resume_id = _upload(client).json()["id"]
    version_id = client.get(f"/v1/resumes/{resume_id}").json()["versions"][0]["id"]
    response = client.post(
        "/v1/analyses",
        json={"resume_version_id": version_id, "career_domain_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 422


def test_admin_endpoints_reject_normal_users(client):
    for path in ("/v1/admin/metrics", "/v1/admin/users", "/v1/admin/settings/scoring"):
        response = client.get(path)
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_can_read_metrics(admin_client):
    response = admin_client.get("/v1/admin/metrics")
    assert response.status_code == 200
    assert response.json()["total_users"] == 1


def test_templates_mark_locked_tiers(client):
    rows = client.get("/v1/templates").json()
    by_slug = {row["slug"]: row for row in rows}
    assert by_slug["ats-friendly"]["locked"] is False
    assert by_slug["experienced-professional"]["locked"] is True


def test_builder_blocks_locked_template(client):
    response = client.post(
        "/v1/generated-resumes",
        json={"template_id": TPL_PREMIUM, "title": "Senior CV"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "TEMPLATE_LOCKED"


def test_builder_autosave_and_export(client):
    created = client.post(
        "/v1/generated-resumes",
        json={"template_id": TPL_ATS, "title": "Frontend CV"},
    )
    assert created.status_code == 201
    generated_id = created.json()["id"]
    content = created.json()["content"]
    content["full_name"] = "Muhammad Haris"
    content["summary"] = "Frontend developer focused on accessible interfaces."

    saved = client.put(f"/v1/generated-resumes/{generated_id}", json=content)
    assert saved.status_code == 200
    assert saved.json()["version"] == 2

    exported = client.post(f"/v1/generated-resumes/{generated_id}/export")
    assert exported.status_code == 202


def test_job_matching_requires_a_paid_plan(client):
    resume_id = _upload(client).json()["id"]
    version_id = client.get(f"/v1/resumes/{resume_id}").json()["versions"][0]["id"]
    response = client.post(
        "/v1/job-matches",
        json={"resume_version_id": version_id, "raw_text": "We need React and TypeScript experience. " * 3},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PLAN_UPGRADE_REQUIRED"


def test_delete_resume_is_soft_and_scoped(client, repos):
    resume_id = _upload(client).json()["id"]
    assert client.delete(f"/v1/resumes/{resume_id}").status_code == 204
    assert client.get(f"/v1/resumes/{resume_id}").status_code == 404
    assert repos.resumes.rows[resume_id]["deleted_at"] is not None
