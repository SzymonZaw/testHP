"""Conservative mapping from hand acquisition views to anatomical regions.

This is a research evidence-linking layer, not a clinical segmentation model.
A photograph can cover several anatomical regions, so mappings are represented as
candidate regions with explicit provenance rather than pretending to know a
pixel-accurate boundary.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegionLink:
    region_id: str
    confidence: float
    method: str
    rationale: str


# These are acquisition-view priors only. They deliberately avoid assigning a
# single precise region to an entire photograph.
VIEW_REGION_PRIORS: dict[str, tuple[str, ...]] = {
    "front": ("palm", "thumb", "index", "middle", "ring", "little", "wrist"),
    "back": ("index", "middle", "ring", "little", "thumb", "wrist"),
    "thumb": ("thumb",),
    "side_left": ("wrist", "little", "ring"),
    "side_right": ("wrist", "index", "thumb"),
}


def map_view_to_regions(view: str | None) -> list[RegionLink]:
    """Return conservative candidate anatomical regions for an acquisition view."""
    normalized = (view or "").strip().lower()
    regions = VIEW_REGION_PRIORS.get(normalized, ())
    if not regions:
        return []

    confidence = 1.0 / len(regions)
    rationale = "acquisition-view prior; no pixel-level anatomical segmentation"
    return [
        RegionLink(
            region_id=region,
            confidence=round(confidence, 6),
            method="view_prior",
            rationale=rationale,
        )
        for region in regions
    ]


def region_links_dict(view: str | None) -> list[dict[str, object]]:
    """Serialize regional links for API/frontend consumers."""
    return [
        {
            "region_id": link.region_id,
            "confidence": link.confidence,
            "mapping_method": link.method,
            "rationale": link.rationale,
        }
        for link in map_view_to_regions(view)
    ]
