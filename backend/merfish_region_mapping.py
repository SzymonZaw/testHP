from __future__ import annotations

from dataclasses import dataclass


UI_REGIONS = ("hand", "wrist", "palm", "thumb", "index", "middle", "ring", "little", "skin_regions")


@dataclass(frozen=True)
class RegionMapping:
    ui_region: str
    anatomic_sites: tuple[str, ...]
    sample_compartments: tuple[str, ...] = ()
    mode: str = "exact"
    note: str = ""


# The MERFISH H5AD contains forearm/elbow/etc., but does not contain hand-digit
# labels. We never silently relabel a forearm cell as a thumb/index/middle/
# ring/little cell. Hand zones therefore remain explicitly unmaterialized until
# an actual hand-local sample is available.
MAPPING: dict[str, RegionMapping] = {
    "hand": RegionMapping("hand", ()),
    "wrist": RegionMapping("wrist", (), note="No exact wrist site is present in the observed H5AD."),
    "palm": RegionMapping("palm", (), note="No exact palm site is present in the observed H5AD."),
    "thumb": RegionMapping("thumb", (), note="No exact thumb site is present in the observed H5AD."),
    "index": RegionMapping("index", (), note="No exact index-finger site is present in the observed H5AD."),
    "middle": RegionMapping("middle", (), note="No exact middle-finger site is present in the observed H5AD."),
    "ring": RegionMapping("ring", (), note="No exact ring-finger site is present in the observed H5AD."),
    "little": RegionMapping("little", (), note="No exact little-finger site is present in the observed H5AD."),
    "skin_regions": RegionMapping(
        "skin_regions",
        ("face", "central scalp", "occipital scalp", "forearm", "abdomen", "postauricular", "knee", "sole", "elbow", "antecubital fossa", "buttocks", "back", "popliteal fossae", "inguinal fold", "chest"),
        mode="multi_site",
        note="All observed skin anatomic sites; not registered to hand geometry.",
    ),
    # Dataset/source selector, not a hand-geometry zone.
    "elbow": RegionMapping("elbow", ("elbow",), note="Exact observed H5AD anatomic_site."),
}


def normalise(value: object) -> str:
    return str(value).strip().casefold() if value is not None else ""


def get_mapping(region: str) -> RegionMapping:
    key = normalise(region)
    if key not in MAPPING:
        raise KeyError(f"Unknown region: {region}")
    return MAPPING[key]


def exact_source_sites(region: str) -> tuple[str, ...]:
    mapping = get_mapping(region)
    if mapping.mode not in {"exact", "multi_site"}:
        return ()
    return mapping.anatomic_sites


def matches_anatomic_site(region: str, anatomic_site: object) -> bool:
    site = normalise(anatomic_site)
    return bool(site) and site in {normalise(x) for x in exact_source_sites(region)}


def matches_sample_compartment(region: str, sample_compartment: object) -> bool:
    compartment = normalise(sample_compartment)
    mapping = get_mapping(region)
    return bool(compartment) and compartment in {normalise(x) for x in mapping.sample_compartments}
