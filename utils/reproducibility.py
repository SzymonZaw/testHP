# utils/reproducibility.py

from __future__ import annotations

import os
import random

import numpy as np
import torch


def set_seed(
    seed: int = 42,
    deterministic: bool = True,
) -> None:
    """
    Set random seeds for reproducible experiments.

    Parameters
    ----------
    seed:
        Random seed.
    deterministic:
        Try to enforce deterministic CUDA behaviour.
    """

    random.seed(seed)

    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    os.environ[
        "PYTHONHASHSEED"
    ] = str(seed)

    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

        try:
            torch.use_deterministic_algorithms(
                True
            )
        except RuntimeError:
            pass


def get_random_state() -> dict:
    """
    Return current random states.

    Useful for debugging and experiment tracking.
    """

    state = {
        "python_random_state": random.getstate(),
        "numpy_random_state": np.random.get_state(),
        "torch_random_state": torch.get_rng_state(),
    }

    if torch.cuda.is_available():
        state["torch_cuda_random_state"] = (
            torch.cuda.get_rng_state_all()
        )

    return state


def restore_random_state(
    state: dict,
) -> None:
    """
    Restore previously captured random states.
    """

    if "python_random_state" in state:
        random.setstate(
            state["python_random_state"]
        )

    if "numpy_random_state" in state:
        np.random.set_state(
            state["numpy_random_state"]
        )

    if "torch_random_state" in state:
        torch.set_rng_state(
            state["torch_random_state"]
        )

    if (
        torch.cuda.is_available()
        and "torch_cuda_random_state" in state
    ):
        torch.cuda.set_rng_state_all(
            state["torch_cuda_random_state"]
        )


def seed_worker(
    worker_id: int,
) -> None:
    """
    Seed a PyTorch DataLoader worker.
    """

    worker_seed = (
        torch.initial_seed()
        % 2**32
    )

    np.random.seed(
        worker_seed
    )

    random.seed(
        worker_seed
    )


def reproducibility_info() -> dict:
    """
    Return environment information relevant
    to reproducibility.
    """

    info = {
        "python_hash_seed": os.environ.get(
            "PYTHONHASHSEED"
        ),
        "torch_version": torch.__version__,
        "numpy_version": np.__version__,
        "cuda_available": torch.cuda.is_available(),
    }

    if torch.cuda.is_available():
        info["cuda_version"] = torch.version.cuda
        info["cuda_device_count"] = (
            torch.cuda.device_count()
        )

        info["cuda_devices"] = [
            torch.cuda.get_device_name(i)
            for i in range(
                torch.cuda.device_count()
            )
        ]

    return info