"""Claim gating: implementation must never masquerade as validation."""

from __future__ import annotations

from dataclasses import dataclass

from .validation import Evidence, EvidenceLevel


@dataclass(frozen=True)
class CapabilityClaim:
    name: str
    minimum_evidence: EvidenceLevel
    clinical_use: bool = False


CLAIMS = {
    "cell_health": CapabilityClaim("cell_health", EvidenceLevel.EXTERNAL_VALIDATION),
    "cell_biological_age": CapabilityClaim("cell_biological_age", EvidenceLevel.EXTERNAL_VALIDATION),
    "long_horizon_prediction": CapabilityClaim("long_horizon_prediction", EvidenceLevel.EXTERNAL_VALIDATION),
    "rejuvenation_candidate_ranking": CapabilityClaim("rejuvenation_candidate_ranking", EvidenceLevel.LONGITUDINAL),
    "clinical_decision": CapabilityClaim("clinical_decision", EvidenceLevel.CLINICAL, clinical_use=True),
}


def claim_status(name: str, evidence: Evidence) -> str:
    claim = CLAIMS[name]
    if evidence.level >= claim.minimum_evidence:
        return "validated" if not claim.clinical_use else "clinical_evidence_required"
    return "research_only"
