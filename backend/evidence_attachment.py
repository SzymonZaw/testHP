from __future__ import annotations

"""Evidence-to-spatial-node attachment for the multiscale hand twin.

An attachment is the explicit bridge between a source asset/evidence item and
one node in the hand hierarchy. It prevents downstream analysis from treating
an arbitrary image or measurement as evidence for a cell without spatial and
longitudinal context.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from psycopg.types.json import Json

from .data_foundation import Provenance, Quality, SpatialReference
from .database import connect, ensure_schema

SpatialLevel = Literal["hand", "anatomy", "tissue", "histology", "cell"]
AttachmentStatus = Literal["candidate", "attached", "rejected"]


@dataclass(frozen=True)
class EvidenceAttachment:
    attachment_id: str
    evidence_id: str
    source_asset_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    spatial_node_id: str
    spatial_level: SpatialLevel
    modality: str
    spatial_reference: SpatialReference
    provenance: Provenance = field(default_factory=Provenance)
    quality: Quality = field(default_factory=Quality)
    status: AttachmentStatus = "attached"
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        for name, value in (
            ("attachment_id", self.attachment_id),
            ("evidence_id", self.evidence_id),
            ("source_asset_id", self.source_asset_id),
            ("subject_id", self.subject_id),
            ("hand_id", self.hand_id),
            ("timepoint_id", self.timepoint_id),
            ("spatial_node_id", self.spatial_node_id),
            ("modality", self.modality),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        self.spatial_reference.validate()
        self.quality.validate()
        if self.status == "attached" and self.spatial_reference.registration_status != "registered":
            raise ValueError("attached evidence requires a registered spatial reference")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def ensure_evidence_attachment_schema() -> None:
    """Create the small persistence boundary without changing existing tables."""
    ensure_schema()
    with connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS evidence_attachments (
                attachment_id TEXT PRIMARY KEY,
                evidence_id TEXT NOT NULL,
                source_asset_id TEXT NOT NULL,
                subject_id TEXT NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
                hand_id TEXT NOT NULL REFERENCES hands(hand_id) ON DELETE CASCADE,
                timepoint_id TEXT NOT NULL,
                spatial_node_id TEXT NOT NULL,
                spatial_level TEXT NOT NULL CHECK (spatial_level IN ('hand','anatomy','tissue','histology','cell')),
                modality TEXT NOT NULL,
                spatial_reference JSONB NOT NULL DEFAULT '{}'::jsonb,
                provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
                quality JSONB NOT NULL DEFAULT '{}'::jsonb,
                status TEXT NOT NULL CHECK (status IN ('candidate','attached','rejected')),
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb
            )"""
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_evidence_attachments_node ON evidence_attachments(spatial_node_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_evidence_attachments_context ON evidence_attachments(subject_id, hand_id, timepoint_id)"
        )
        conn.commit()


def register_evidence_attachment(attachment: EvidenceAttachment) -> EvidenceAttachment:
    attachment.validate()
    ensure_evidence_attachment_schema()
    with connect() as conn:
        conn.execute(
            """INSERT INTO evidence_attachments
               (attachment_id, evidence_id, source_asset_id, subject_id, hand_id,
                timepoint_id, spatial_node_id, spatial_level, modality,
                spatial_reference, provenance, quality, status, metadata)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (attachment_id) DO UPDATE SET
                 evidence_id=EXCLUDED.evidence_id,
                 source_asset_id=EXCLUDED.source_asset_id,
                 spatial_node_id=EXCLUDED.spatial_node_id,
                 spatial_level=EXCLUDED.spatial_level,
                 modality=EXCLUDED.modality,
                 spatial_reference=EXCLUDED.spatial_reference,
                 provenance=EXCLUDED.provenance,
                 quality=EXCLUDED.quality,
                 status=EXCLUDED.status,
                 metadata=EXCLUDED.metadata""",
            (
                attachment.attachment_id,
                attachment.evidence_id,
                attachment.source_asset_id,
                attachment.subject_id,
                attachment.hand_id,
                attachment.timepoint_id,
                attachment.spatial_node_id,
                attachment.spatial_level,
                attachment.modality,
                Json(asdict(attachment.spatial_reference)),
                Json(asdict(attachment.provenance)),
                Json(asdict(attachment.quality)),
                attachment.status,
                Json(attachment.metadata),
            ),
        )
        conn.commit()
    return attachment
