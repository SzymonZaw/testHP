from __future__ import annotations

SKIN_OBSERVATION_ONTOLOGY = {
    "regions": ["dorsal_hand", "palmar_hand", "finger", "nail", "wrist", "skin_patch"],
    "observation_types": [
        "color", "brightness", "contrast", "texture", "pigmentation",
        "vascular_pattern", "redness", "lesion_presence", "lesion_size",
        "surface_irregularity", "nail_appearance", "swelling", "scar_like_change",
    ],
    "categories": ["normal_skin", "aging_skin", "lesions", "pathology", "unclassified"],
    "evidence_levels": ["observed", "derived", "interpreted"],
    "interpretation_policy": {
        "diagnosis_allowed": False,
        "disease_claim_allowed": False,
        "missing_data": "unavailable",
    },
}


def ontology_snapshot() -> dict:
    return SKIN_OBSERVATION_ONTOLOGY.copy()
