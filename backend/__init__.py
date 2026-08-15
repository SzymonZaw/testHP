# Import the FastAPI app first, then register optional analysis routes.
# This keeps `uvicorn backend.app:app` as the single application entrypoint.
from . import app as _app  # noqa: F401
from . import hand_analysis as _hand_analysis  # noqa: F401
from . import hand_roi as _hand_roi  # noqa: F401
