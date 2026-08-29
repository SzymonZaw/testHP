"""Validation and readiness reporting for the TestHP multiscale user package.

The validator is intentionally conservative: it reports missing or insufficient
inputs instead of inventing values. It validates the package structure and the
modality-specific minimums declared in the v1 input requirements.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


MODALITY_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "hand_images": ("uri", "format", "provenance", "acquisition.laterality", "acquisition.anatomical_site", "acquisition.acquisition_time"),
    "hand_video": ("uri", "format", "provenance", "acquisition.laterality", "acquisition.acquisition_time"),
    "hand_3d": ("uri", "format", "provenance", "acquisition.laterality", "acquisition.acquisition_time", "metadata.coordinate_system"),
    "tissue_wsi": ("uri", "format", "provenance", "sample_id", "metadata.tissue_type", "metadata.specimen_id", "metadata.acquisition_metadata"),
    "microscopy": ("uri", "format", "provenance", "sample_id"),
    "single_cell_rna": ("uri", "format", "provenance", "sample_id", "metadata.gene_identifier_namespace"),
    "bulk_rna": ("uri", "format", "provenance", "sample_id", "metadata.gene_identifier_namespace"),
    "genomics": ("uri", "format", "provenance", "sample_id", "metadata.genome_build"),
    "proteomics": ("uri", "format", "provenance", "sample_id", "metadata.protein_identifier_namespace"),
    "epigenetics": ("uri", "format", "provenance", "sample_id", "metadata.assay_type"),
    "clinical_context": ("uri", "format", "provenance", "metadata.structured_metadata"),
    "ground_truth": ("uri", "format", "provenance", "metadata.label", "metadata.label_definition", "metadata.label_source", "metadata.reference_timepoint"),
}

SUPPORTED_KINDS = frozenset(MODALITY_REQUIREMENTS)
REQUIRED_TOP_LEVEL = ("subject", "acquisition", "inputs")


@dataclass(frozen=True)
class Finding:
    severity: str  # error | warning | info
    code: str
    message: str
    input_id: str | None = None
    kind: str | None = None


@dataclass
class ReadinessReport:
    valid_contract: bool = True
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "warning"]

    @property
    def accepted_inputs(self) -> list[Finding]:
        return [f for f in self.findings if f.code == "INPUT_ACCEPTED"]

    @property
    def ready_for_any_processing(self) -> bool:
        return self.valid_contract and bool(self.accepted_inputs)

    @property
    def status(self) -> str:
        if not self.valid_contract:
            return "INVALID"
        if not self.accepted_inputs:
            return "INCOMPLETE"
        if self.warnings:
            return "READY_WITH_WARNINGS"
        return "READY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "valid_contract": self.valid_contract,
            "ready_for_any_processing": self.ready_for_any_processing,
            "accepted_input_count": len(self.accepted_inputs),
            "errors": [f.__dict__ for f in self.errors],
            "warnings": [f.__dict__ for f in self.warnings],
            "findings": [f.__dict__ for f in self.findings],
        }


def _get_path(obj: Any, path: str) -> Any:
    current = obj
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _missing(obj: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    return [k for k in keys if _get_path(obj, k) in (None, "")]


def _validate_provenance(item: dict[str, Any]) -> bool:
    provenance = item.get("provenance")
    return isinstance(provenance, dict) and provenance.get("source_type") in {
        "user", "clinical", "research_dataset", "derived"
    }


def validate_user_package(package: dict[str, Any]) -> ReadinessReport:
    """Validate a parsed v1 package and report what can be processed.

    This function checks metadata only. It deliberately does not inspect or
    interpret the referenced scientific files and therefore cannot establish
    scientific or clinical validity.
    """
    report = ReadinessReport()
    if not isinstance(package, dict):
        report.valid_contract = False
        report.findings.append(Finding("error", "PACKAGE_NOT_OBJECT", "User package must be a JSON object."))
        return report

    missing_top = _missing(package, REQUIRED_TOP_LEVEL)
    if missing_top:
        report.valid_contract = False
        report.findings.append(Finding("error", "MISSING_TOP_LEVEL", f"Missing top-level fields: {', '.join(missing_top)}."))
        return report

    subject = package["subject"]
    acquisition = package["acquisition"]
    inputs = package["inputs"]
    if not isinstance(subject, dict) or not subject.get("subject_id"):
        report.valid_contract = False
        report.findings.append(Finding("error", "INVALID_SUBJECT", "subject.subject_id is required."))
    if not isinstance(acquisition, dict) or not acquisition.get("timepoint_id") or not acquisition.get("acquisition_time"):
        report.valid_contract = False
        report.findings.append(Finding("error", "INVALID_ACQUISITION", "acquisition.timepoint_id and acquisition.acquisition_time are required."))
    if not isinstance(inputs, list) or not inputs:
        report.valid_contract = False
        report.findings.append(Finding("error", "NO_INPUTS", "At least one input is required."))
        return report

    for item in inputs:
        if not isinstance(item, dict):
            report.valid_contract = False
            report.findings.append(Finding("error", "INPUT_NOT_OBJECT", "Each input must be an object."))
            continue

        input_id = item.get("input_id")
        kind = item.get("kind")
        if not input_id or not kind:
            report.valid_contract = False
            report.findings.append(Finding("error", "INVALID_INPUT_IDENTITY", "Each input requires input_id and kind.", input_id=input_id, kind=kind))
            continue
        if kind not in SUPPORTED_KINDS:
            report.valid_contract = False
            report.findings.append(Finding("error", "UNSUPPORTED_KIND", f"Unsupported input kind: {kind}.", input_id=input_id, kind=kind))
            continue

        missing = _missing(item, MODALITY_REQUIREMENTS[kind])
        if "provenance" not in missing and not _validate_provenance(item):
            missing.append("provenance.source_type")
        if missing:
            report.findings.append(Finding("warning", "INPUT_INCOMPLETE", f"Missing modality requirements: {', '.join(missing)}.", input_id=input_id, kind=kind))
        else:
            report.findings.append(Finding("info", "INPUT_ACCEPTED", f"{kind} package metadata is complete for the v1 minimum contract.", input_id=input_id, kind=kind))

        if kind == "ground_truth" and not missing:
            report.findings.append(Finding("info", "GROUND_TRUTH_PRESENT", "Ground truth is supplied as reference evidence; it is not inferred from the prediction.", input_id=input_id, kind=kind))

    return report


def validate_user_package_file(path: str | Path) -> ReadinessReport:
    with Path(path).open("r", encoding="utf-8") as handle:
        return validate_user_package(json.load(handle))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate a TestHP v1 user input package")
    parser.add_argument("package", help="Path to the user input JSON")
    args = parser.parse_args()
    print(json.dumps(validate_user_package_file(args.package).to_dict(), indent=2, ensure_ascii=False))
