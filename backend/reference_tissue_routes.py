from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/reference/tissue", tags=["reference-tissue"])

_HAND_REFERENCE = "nih-hand-template-3DPX-017237"
_SOURCES = {
    "human-skin-spatial-census": {
        "id": "human-skin-spatial-census",
        "accessions": ["S-BIAD2376"],
        "label": "Single-cell spatial transcriptomic analysis of human skin anatomy",
        "organism": "Homo sapiens",
        "modality": "spatial_transcriptomics",
        "spatialMethod": "MERFISH",
        "coordinateScope": "sample_local",
        "handReferenceId": _HAND_REFERENCE,
        "registrationStatus": "unregistered_to_hand",
        "registrationReadiness": "anatomical_match_verified_transform_missing",
        "verifiedAnatomicalSites": [
            {"regionId": "palm", "sourceSite": "palm", "approxCellCount": 2600},
            {"regionId": "hand", "sourceSite": "hand", "approxCellCount": 1148},
        ],
        "dataAvailability": {
            "raw": "https://www.ebi.ac.uk/biostudies/arrayexpress/studies/S-BIAD2376",
            "processed": "https://doi.org/10.5281/zenodo.16795569",
            "interactive": "https://rstudio-connect.hpc.mssm.edu/humanskin-spatialcensus/",
            "publication": "https://doi.org/10.1038/s41588-026-02552-8",
        },
    },
    "geo-skin-spatial-visium": {
        "id": "geo-skin-spatial-visium",
        "accessions": ["GSM8238470"],
        "label": "GEO human skin spatial transcriptomics sample",
        "organism": "Homo sapiens",
        "modality": "spatial_transcriptomics",
        "spatialMethod": "10x Genomics Visium",
        "coordinateScope": "sample_local",
        "handReferenceId": _HAND_REFERENCE,
        "registrationStatus": "unregistered_to_hand",
        "registrationReadiness": "no_verified_hand_registration",
        "verifiedAnatomicalSites": [],
        "dataAvailability": {
            "geo": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM8238470",
        },
    },
    "hubmap-human-reference-atlas": {
        "id": "hubmap-human-reference-atlas",
        "accessions": [],
        "label": "HuBMAP Human Reference Atlas resources",
        "organism": "Homo sapiens",
        "modality": "multimodal_tissue_reference",
        "spatialMethod": None,
        "coordinateScope": "resource_dependent",
        "handReferenceId": _HAND_REFERENCE,
        "registrationStatus": "unregistered_to_hand",
        "registrationReadiness": "resource_dependent",
        "verifiedAnatomicalSites": [],
        "dataAvailability": {"portal": "https://hubmapconsortium.org/"},
    },
}


@router.get("/sources")
def list_reference_tissue_sources() -> dict:
    return {
        "handReferenceId": _HAND_REFERENCE,
        "sources": list(_SOURCES.values()),
    }


@router.get("/{source_id}")
def reference_tissue_manifest(source_id: str) -> dict:
    source = _SOURCES.get(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="reference tissue source not found")
    return {
        "source": source,
        "dataLoadStatus": "manifest_only",
        "tissueIds": [],
        "spatialCoordinates": [],
        "transform": None,
        "note": "Large spatial data are not fetched automatically. A verified transform into the NIH hand-template frame is not established.",
    }
