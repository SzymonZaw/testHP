# utils/device.py

from __future__ import annotations

from typing import Optional

import torch


def get_device(
    preferred: Optional[str] = None,
) -> torch.device:
    """
    Select the best available computation device.

    Priority:
        1. explicitly requested device
        2. CUDA
        3. Apple MPS
        4. CPU

    Parameters
    ----------
    preferred:
        Optional device name, e.g. "cuda", "cpu", "mps".

    Returns
    -------
    torch.device
    """

    if preferred is not None:
        preferred = preferred.lower()

        if preferred == "cuda":
            if torch.cuda.is_available():
                return torch.device("cuda")

            raise RuntimeError(
                "CUDA was requested, but CUDA is not available."
            )

        if preferred == "mps":
            if hasattr(torch.backends, "mps"):
                if torch.backends.mps.is_available():
                    return torch.device("mps")

            raise RuntimeError(
                "MPS was requested, but MPS is not available."
            )

        if preferred == "cpu":
            return torch.device("cpu")

        raise ValueError(
            f"Unsupported device: {preferred}"
        )

    if torch.cuda.is_available():
        return torch.device("cuda")

    if hasattr(torch.backends, "mps"):
        if torch.backends.mps.is_available():
            return torch.device("mps")

    return torch.device("cpu")


def device_summary(
    device: Optional[torch.device] = None,
) -> dict:
    """
    Return information about the selected device.
    """

    if device is None:
        device = get_device()

    summary = {
        "device": str(device),
        "cuda_available": torch.cuda.is_available(),
        "mps_available": (
            hasattr(torch.backends, "mps")
            and torch.backends.mps.is_available()
        ),
        "cpu_available": True,
    }

    if device.type == "cuda":
        summary["cuda_device_count"] = torch.cuda.device_count()
        summary["cuda_device_name"] = torch.cuda.get_device_name(
            device
        )

        summary["cuda_memory_allocated"] = (
            torch.cuda.memory_allocated(device)
        )

        summary["cuda_memory_reserved"] = (
            torch.cuda.memory_reserved(device)
        )

    return summary


def move_to_device(
    obj,
    device: torch.device,
):
    """
    Move a tensor or module to the selected device.

    Works with objects implementing .to().
    """

    if hasattr(obj, "to"):
        return obj.to(device)

    raise TypeError(
        f"Object of type {type(obj)} cannot be moved to device."
    )


def clear_cuda_cache() -> None:
    """
    Clear CUDA memory cache when CUDA is available.
    """

    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def set_cuda_device(
    index: int,
) -> None:
    """
    Select CUDA device by index.
    """

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available.")

    if index < 0 or index >= torch.cuda.device_count():
        raise ValueError(
            f"Invalid CUDA device index: {index}"
        )

    torch.cuda.set_device(index)