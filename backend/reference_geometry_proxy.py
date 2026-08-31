from __future__ import annotations

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from urllib.request import Request, urlopen

NIH_REFERENCE_GLB_URL = (
    "https://3d.nih.gov/api/submissions/23310/runs/"
    "c054b0b1-404c-4f43-b6a7-ddff98215e52/output-files/511811"
)
ROUTE_PATH = "/api/reference-hand/3dpx-017237.glb"


def register_reference_geometry_proxy(app) -> None:
    if any(getattr(route, "path", None) == ROUTE_PATH for route in app.routes):
        return

    @app.get(ROUTE_PATH, include_in_schema=False)
    def reference_hand_geometry():
        try:
            request = Request(
                NIH_REFERENCE_GLB_URL,
                headers={"User-Agent": "testHP-reference-proxy/1.0", "Range": "bytes=0-0"},
            )
            with urlopen(request, timeout=10) as response:
                if getattr(response, "status", 200) >= 400:
                    raise HTTPException(status_code=502, detail="NIH reference geometry unavailable")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=502, detail="NIH reference geometry unavailable") from exc

        def chunks():
            try:
                request = Request(NIH_REFERENCE_GLB_URL, headers={"User-Agent": "testHP-reference-proxy/1.0"})
                with urlopen(request, timeout=20) as response:
                    while chunk := response.read(1024 * 1024):
                        yield chunk
            except Exception as exc:
                print(f"[reference-proxy] NIH geometry fetch failed: {exc}")

        return StreamingResponse(
            chunks(),
            media_type="model/gltf-binary",
            headers={
                "Cache-Control": "public, max-age=3600",
                "X-TestHP-Reference-Provenance": "public_reference",
                "X-TestHP-Reference-Source": "nih-hand-template-3DPX-017237",
            },
        )
