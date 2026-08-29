from __future__ import annotations

"""Small, dependency-free clients for public reference-data catalogs.

These clients intentionally return metadata and download URLs rather than
silently copying large datasets into testHP. Dataset-specific terms remain
attached to the returned provenance record.
"""

import json
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


class ReferenceDataError(RuntimeError):
    pass


def _get_json(url: str, *, timeout: float = 20.0) -> dict:
    request = Request(url, headers={"User-Agent": "testHP-scientific-integrations/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # pragma: no cover - network conditions vary
        raise ReferenceDataError(f"reference data request failed: {url}") from exc


def hca_project_metadata(project_uuid: str) -> dict:
    """Fetch HCA Data Portal project metadata by UUID."""
    if not project_uuid.strip():
        raise ValueError("project_uuid is required")
    url = "https://data.humancellatlas.org/explore/projects/" + quote(project_uuid, safe="")
    return {"source": "hca", "project_uuid": project_uuid, "url": url}


def cellxgene_census_query(*, organism: str = "Homo sapiens", tissue: str | None = None) -> dict:
    """Build a CELLxGENE Census query descriptor without downloading data."""
    filters = [f"organism == '{organism.replace(chr(39), chr(39) * 2)}'"]
    if tissue:
        filters.append(f"tissue_general == '{tissue.replace(chr(39), chr(39) * 2)}'")
    return {
        "source": "cellxgene",
        "endpoint": "https://cellxgene.cziscience.com/",
        "query": " and ".join(filters),
        "parameters": {"organism": organism, "tissue": tissue},
    }


def arc_virtual_cell_atlas_descriptor() -> dict:
    return {
        "source": "arc-virtual-cell-atlas",
        "url": "https://arcinstitute.org/tools/virtualcellatlas",
        "role": "reference_and_perturbation_data",
        "license_note": "Atlas data are described by Arc as CC0; verify terms for linked datasets.",
    }


def alphafold_db_url(identifier: str) -> str:
    """Return an AlphaFold DB entry URL for a UniProt accession."""
    if not identifier.strip():
        raise ValueError("identifier is required")
    return "https://alphafold.ebi.ac.uk/entry/" + quote(identifier.strip(), safe="")


def query_url(base: str, params: dict[str, str]) -> str:
    """Build a deterministic URL for provenance/debug output."""
    return base.rstrip("?") + "?" + urlencode(params)
