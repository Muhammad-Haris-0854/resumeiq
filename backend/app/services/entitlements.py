"""Plan entitlements and quota enforcement.

This is the single place that decides what a user may do. Endpoints call `require_feature` and
`consume_quota`; nothing else reads a plan name.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from app.core.errors import Forbidden, QuotaExceeded
from app.models.enums import PLAN_FEATURES, PlanCode


@dataclass(frozen=True)
class Entitlements:
    plan: PlanCode
    features: dict[str, Any]
    analysis_quota: int
    analyses_used: int
    max_resumes: int

    @property
    def analyses_remaining(self) -> int:
        return max(0, self.analysis_quota - self.analyses_used)

    @property
    def period_start(self) -> str:
        return date.today().replace(day=1).isoformat()

    def allows(self, feature: str) -> bool:
        return bool(self.features.get(feature, False))

    def as_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan,
            "analysis_quota": self.analysis_quota,
            "analyses_used": self.analyses_used,
            "analyses_remaining": self.analyses_remaining,
            "max_resumes": self.max_resumes,
            "features": self.features,
            "period_start": self.period_start,
        }


def resolve_entitlements(plan: PlanCode, analyses_used: int) -> Entitlements:
    features = dict(PLAN_FEATURES.get(plan, PLAN_FEATURES[PlanCode.FREE]))
    return Entitlements(
        plan=plan,
        features=features,
        analysis_quota=int(features.get("analysis_quota", 0)),
        analyses_used=analyses_used,
        max_resumes=int(features.get("max_resumes", 1)),
    )


def require_feature(entitlements: Entitlements, feature: str) -> None:
    if not entitlements.allows(feature):
        raise Forbidden(
            f"Your {entitlements.plan.value.title()} plan does not include this feature. "
            "Upgrade to continue.",
            code="PLAN_UPGRADE_REQUIRED",
            details={"feature": feature, "plan": entitlements.plan.value},
        )


def assert_quota(entitlements: Entitlements) -> None:
    if entitlements.analyses_remaining <= 0:
        raise QuotaExceeded(
            f"You have used all {entitlements.analysis_quota} analyses on the "
            f"{entitlements.plan.value.title()} plan this month.",
            code="QUOTA_EXCEEDED",
            details={
                "plan": entitlements.plan.value,
                "quota": entitlements.analysis_quota,
                "used": entitlements.analyses_used,
                "period_start": entitlements.period_start,
            },
        )


def assert_resume_limit(entitlements: Entitlements, current_count: int) -> None:
    if current_count >= entitlements.max_resumes:
        raise Forbidden(
            f"The {entitlements.plan.value.title()} plan stores up to {entitlements.max_resumes} "
            "resumes. Delete one or upgrade.",
            code="RESUME_LIMIT_REACHED",
            details={"limit": entitlements.max_resumes, "current": current_count},
        )
