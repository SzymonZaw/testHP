import os
import yaml
import json
import traceback
from datetime import datetime

import numpy as np
import torch
from PIL import Image

# ============================================================
# KONFIGURACJA
# ============================================================

CONFIG_PATH = "config.yaml"

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
else:
    config = {}

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

IMAGE_PATH = config.get(
    "image_path",
    "test.jpg"
)

OUTPUT_DIR = config.get(
    "output_dir",
    "outputs"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# LOGGER
# ============================================================

try:
    from utils.logger import get_logger
    logger = get_logger("main")
except Exception:
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )
    logger = logging.getLogger("main")

# ============================================================
# NARZĘDZIA
# ============================================================

def safe_import(module_name, function_name=None):
    try:
        module = __import__(module_name, fromlist=["*"])
        if function_name:
            return getattr(module, function_name)
        return module
    except Exception as e:
        logger.warning(
            f"Nie można załadować {module_name}: {e}"
        )
        return None


def save_json(data, filename):
    path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        if isinstance(obj, torch.Tensor):
            return obj.detach().cpu().tolist()

        if isinstance(obj, (np.float32, np.float64)):
            return float(obj)

        if isinstance(obj, (np.int32, np.int64)):
            return int(obj)

        return str(obj)

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
            default=convert
        )

    logger.info(
        f"Zapisano: {path}"
    )


# ============================================================
# START
# ============================================================

logger.info("=" * 70)
logger.info("SYSTEM ANALIZY BIOLOGICZNEJ")
logger.info("=" * 70)
logger.info(f"Urządzenie: {DEVICE}")
logger.info(f"CUDA: {torch.cuda.is_available()}")
logger.info(f"PyTorch: {torch.__version__}")
logger.info(f"Obraz: {IMAGE_PATH}")

# ============================================================
# WCZYTANIE OBRAZU
# ============================================================

if not os.path.exists(IMAGE_PATH):
    raise FileNotFoundError(
        f"Nie znaleziono obrazu: {IMAGE_PATH}"
    )

pil_image = Image.open(
    IMAGE_PATH
).convert("RGB")

image = np.array(
    pil_image
)

logger.info(
    f"Obraz: {image.shape}"
)

# ============================================================
# WYNIKI SYSTEMU
# ============================================================

results = {
    "metadata": {
        "timestamp": datetime.now().isoformat(),
        "device": DEVICE,
        "image_path": IMAGE_PATH
    },
    "image": {},
    "cells": {},
    "rna": {},
    "hand": {},
    "fusion": {},
    "aging": {},
    "abnormality": {},
    "pathology": {},
    "risk": {},
    "intervention": {},
    "digital_twin": {},
    "decision": {}
}

# ============================================================
# SAM2
# ============================================================

logger.info("")
logger.info("========== SAM2 ==========")

try:
    sam2_module = safe_import(
        "models.sam2_model"
    )

    if sam2_module and hasattr(
        sam2_module,
        "SAM2Model"
    ):
        sam2_model = sam2_module.SAM2Model(
            config=config,
            device=DEVICE
        )

        sam2_result = sam2_model.predict(
            image
        )

    elif sam2_module and hasattr(
        sam2_module,
        "segment"
    ):
        sam2_result = sam2_module.segment(
            image,
            config
        )

    else:
        logger.warning(
            "Brak interfejsu SAM2Model/segment()."
        )
        sam2_result = None

    if sam2_result is not None:
        results["image"]["sam2"] = sam2_result
        logger.info("SAM2: OK")
    else:
        results["image"]["sam2"] = {
            "status": "NOT_AVAILABLE"
        }

except Exception as e:
    logger.error(
        f"SAM2 błąd: {e}"
    )
    results["image"]["sam2"] = {
        "status": "ERROR",
        "error": str(e)
    }

# ============================================================
# CELLPOSE
# ============================================================

logger.info("")
logger.info("========== CELLPOSE ==========")

try:
    cellpose_module = safe_import(
        "models.cellpose_model"
    )

    if cellpose_module and hasattr(
        cellpose_module,
        "CellposeModel"
    ):
        cellpose_model = cellpose_module.CellposeModel(
            config=config,
            device=DEVICE
        )

        cellpose_result = cellpose_model.predict(
            image
        )

    elif cellpose_module and hasattr(
        cellpose_module,
        "segment"
    ):
        cellpose_result = cellpose_module.segment(
            image,
            config
        )

    else:
        logger.warning(
            "Brak interfejsu CellposeModel/segment()."
        )
        cellpose_result = None

    if cellpose_result is not None:
        results["cells"]["cellpose"] = cellpose_result
        logger.info("Cellpose: OK")
    else:
        results["cells"]["cellpose"] = {
            "status": "NOT_AVAILABLE"
        }

except Exception as e:
    logger.error(
        f"Cellpose błąd: {e}"
    )

    results["cells"]["cellpose"] = {
        "status": "ERROR",
        "error": str(e)
    }

# ============================================================
# MONAI
# ============================================================

logger.info("")
logger.info("========== MONAI ==========")

try:
    monai_module = safe_import(
        "models.monai_pipeline"
    )

    if monai_module and hasattr(
        monai_module,
        "preprocess"
    ):
        monai_result = monai_module.preprocess(
            image
        )

    elif monai_module and hasattr(
        monai_module,
        "MONAIPipeline"
    ):
        monai_model = monai_module.MONAIPipeline(
            config=config
        )

        monai_result = monai_model.process(
            image
        )

    else:
        logger.warning(
            "Brak interfejsu MONAI."
        )
        monai_result = None

    if monai_result is not None:
        results["image"]["monai"] = {
            "status": "OK",
            "shape": getattr(
                monai_result,
                "shape",
                None
            )
        }

        logger.info(
            f"MONAI: OK | {getattr(monai_result, 'shape', None)}"
        )

    else:
        results["image"]["monai"] = {
            "status": "NOT_AVAILABLE"
        }

except Exception as e:
    logger.error(
        f"MONAI błąd: {e}"
    )

    results["image"]["monai"] = {
        "status": "ERROR",
        "error": str(e)
    }

# ============================================================
# DINOv2
# ============================================================

logger.info("")
logger.info("========== DINOv2 ==========")

try:
    dinov2_module = safe_import(
        "models.dinov2_model"
    )

    if dinov2_module and hasattr(
        dinov2_module,
        "DINOv2Model"
    ):
        dinov2_model = dinov2_module.DINOv2Model(
            device=DEVICE
        )

        embedding = dinov2_model.encode(
            pil_image
        )

    elif dinov2_module and hasattr(
        dinov2_module,
        "get_embedding"
    ):
        embedding = dinov2_module.get_embedding(
            pil_image,
            device=DEVICE
        )

    else:
        embedding = None

    if embedding is not None:
        results["image"]["dinov2"] = {
            "status": "OK",
            "embedding_shape": list(
                embedding.shape
            ) if hasattr(
                embedding,
                "shape"
            ) else None
        }

        logger.info(
            f"DINOv2: OK | {getattr(embedding, 'shape', None)}"
        )

    else:
        results["image"]["dinov2"] = {
            "status": "NOT_AVAILABLE"
        }

except Exception as e:
    logger.error(
        f"DINOv2 błąd: {e}"
    )

    results["image"]["dinov2"] = {
        "status": "ERROR",
        "error": str(e)
    }

# ============================================================
# SCANPY
# ============================================================

logger.info("")
logger.info("========== SCANPY / RNA ==========")

try:
    scanpy_module = safe_import(
        "models.scanpy_model"
    )

    if scanpy_module and hasattr(
        scanpy_module,
        "ScanpyModel"
    ):
        scanpy_model = scanpy_module.ScanpyModel(
            config=config
        )

        rna_result = scanpy_model.analyze()

    elif scanpy_module and hasattr(
        scanpy_module,
        "analyze"
    ):
        rna_result = scanpy_module.analyze(
            config
        )

    else:
        rna_result = None

    if rna_result is not None:
        results["rna"] = rna_result
        logger.info("Scanpy: OK")
    else:
        results["rna"] = {
            "status": "NOT_AVAILABLE"
        }

except Exception as e:
    logger.error(
        f"Scanpy błąd: {e}"
    )

    results["rna"] = {
        "status": "ERROR",
        "error": str(e)
    }

# ============================================================
# MEDIAPIPE + MANO
# ============================================================

logger.info("")
logger.info("========== HAND ==========")

try:
    hand_module = safe_import(
        "models.hand_model"
    )

    if hand_module and hasattr(
        hand_module,
        "HandModel"
    ):
        hand_model = hand_module.HandModel(
            config=config,
            device=DEVICE
        )

        hand_result = hand_model.analyze(
            pil_image
        )

    elif hand_module and hasattr(
        hand_module,
        "analyze_hand"
    ):
        hand_result = hand_module.analyze_hand(
            pil_image,
            config
        )

    else:
        hand_result = None

    if hand_result is not None:
        results["hand"] = hand_result
        logger.info("MediaPipe/MANO: OK")
    else:
        results["hand"] = {
            "status": "NOT_AVAILABLE"
        }

except Exception as e:
    logger.error(
        f"Hand błąd: {e}"
    )

    results["hand"] = {
        "status": "ERROR",
        "error": str(e)
    }

# ============================================================
# MULTIMODAL FUSION
# ============================================================

logger.info("")
logger.info("========== MULTIMODAL FUSION ==========")

try:
    fusion_module = safe_import(
        "models.fusion_model"
    )

    if fusion_module and hasattr(
        fusion_module,
        "FusionModel"
    ):
        fusion_model = fusion_module.FusionModel(
            config=config,
            device=DEVICE
        )

        fusion_result = fusion_model.combine(
            results
        )

    elif fusion_module and hasattr(
        fusion_module,
        "fuse"
    ):
        fusion_result = fusion_module.fuse(
            results,
            config
        )

    else:
        fusion_result = {
            "status": "NOT_IMPLEMENTED"
        }

    results["fusion"] = fusion_result

    logger.info("Fusion: OK")

except Exception as e:
    logger.error(
        f"Fusion błąd: {e}"
    )

    results["fusion"] = {
        "status": "ERROR",
        "error": str(e)
    }

# ============================================================
# BIOLOGICAL AGE
# ============================================================

logger.info("")
logger.info("========== BIOLOGICAL AGE ==========")

try:
    aging_module = safe_import(
        "models.aging_model"
    )

    if aging_module and hasattr(
        aging_module,
        "AgingModel"
    ):
        aging_model = aging_module.AgingModel(
            config=config,
            device=DEVICE
        )

        aging_result = aging_model.predict(
            results["fusion"]
        )

    elif aging_module and hasattr(
        aging_module,
        "predict_age"
    ):
        aging_result = aging_module.predict_age(
            results["fusion"],
            config
        )

    else:
        aging_result = {
            "status": "NOT_IMPLEMENTED"
        }

    results["aging"] = aging_result

    logger.info("Biological age: OK")

except Exception as e:
    logger.error(
        f"Age model błąd: {e}"
    )

    results["aging"] = {
        "status": "ERROR",
        "error": str(e)
    }

# ============================================================
# ABNORMALITY DETECTION
# ============================================================

logger.info("")
logger.info("========== ABNORMALITY ==========")

try:
    abnormality_module = safe_import(
        "models.abnormality_model"
    )

    if abnormality_module and hasattr(
        abnormality_module,
        "AbnormalityModel"
    ):
        abnormality_model = abnormality_module.AbnormalityModel(
            config=config,
            device=DEVICE
        )

        abnormality_result = abnormality_model.predict(
            results["fusion"]
        )

    elif abnormality_module and hasattr(
        abnormality_module,
        "detect"
    ):
        abnormality_result = abnormality_module.detect(
            results["fusion"],
            config
        )

    else:
        abnormality_result = {
            "status": "NOT_IMPLEMENTED"
        }

    results["abnormality"] = abnormality_result

    logger.info(
        "Abnormality detection: OK"
    )

except Exception as e:
    logger.error(
        f"Abnormality błąd: {e}"
    )

    results["abnormality"] = {
        "status": "ERROR",
        "error": str(e)
    }

# ============================================================
# PATHOLOGY
# ============================================================

logger.info("")
logger.info("========== PATHOLOGY ==========")

try:
    pathology_module = safe_import(
        "models.pathology_model"
    )

    if pathology_module and hasattr(
        pathology_module,
        "PathologyModel"
    ):
        pathology_model = pathology_module.PathologyModel(
            config=config,
            device=DEVICE
        )

        pathology_result = pathology_model.predict(
            results["fusion"],
            results["abnormality"]
        )

    elif pathology_module and hasattr(
        pathology_module,
        "analyze"
    ):
        pathology_result = pathology_module.analyze(
            results,
            config
        )

    else:
        pathology_result = {
            "status": "NOT_IMPLEMENTED"
        }

    results["pathology"] = pathology_result

    logger.info("Pathology: OK")

except Exception as e:
    logger.error(
        f"Pathology błąd: {e}"
    )

    results["pathology"] = {
        "status": "ERROR",
        "error": str(e)
    }

# ============================================================
# RISK
# ============================================================

logger.info("")
logger.info("========== RISK ==========")

try:
    risk_module = safe_import(
        "models.risk_model"
    )

    if risk_module and hasattr(
        risk_module,
        "RiskModel"
    ):
        risk_model = risk_module.RiskModel(
            config=config,
            device=DEVICE
        )

        risk_result = risk_model.predict(
            aging=results["aging"],
            abnormality=results["abnormality"],
            pathology=results["pathology"]
        )

    elif risk_module and hasattr(
        risk_module,
        "calculate_risk"
    ):
        risk_result = risk_module.calculate_risk(
            results,
            config
        )

    else:
        risk_result = {
            "status": "NOT_IMPLEMENTED"
        }

    results["risk"] = risk_result

    logger.info("Risk model: OK")

except Exception as e:
    logger.error(
        f"Risk błąd: {e}"
    )

    results["risk"] = {
        "status": "ERROR",
        "error": str(e)
    }

# ============================================================
# INTERVENTION
# ============================================================

logger.info("")
logger.info("========== INTERVENTION ==========")

try:
    intervention_module = safe_import(
        "models.intervention_model"
    )

    if intervention_module and hasattr(
        intervention_module,
        "InterventionModel"
    ):
        intervention_model = intervention_module.InterventionModel(
            config=config,
            device=DEVICE
        )

        intervention_result = intervention_model.predict(
            aging=results["aging"],
            risk=results["risk"]
        )

    elif intervention_module and hasattr(
        intervention_module,
        "evaluate"
    ):
        intervention_result = intervention_module.evaluate(
            results,
            config
        )

    else:
        intervention_result = {
            "status": "NOT_IMPLEMENTED"
        }

    results["intervention"] = intervention_result

    logger.info(
        "Intervention model: OK"
    )

except Exception as e:
    logger.error(
        f"Intervention błąd: {e}"
    )

    results["intervention"] = {
        "status": "ERROR",
        "error": str(e)
    }

# ============================================================
# DIGITAL TWIN
# ============================================================

logger.info("")
logger.info("========== DIGITAL TWIN ==========")

try:
    twin_module = safe_import(
        "models.digital_twin"
    )

    if twin_module and hasattr(
        twin_module,
        "DigitalTwin"
    ):
        twin = twin_module.DigitalTwin(
            config=config
        )

        twin_result = twin.update(
            results
        )

    elif twin_module and hasattr(
        twin_module,
        "create_twin"
    ):
        twin_result = twin_module.create_twin(
            results,
            config
        )

    else:
        twin_result = {
            "status": "NOT_IMPLEMENTED"
        }

    results["digital_twin"] = twin_result

    logger.info(
        "Digital Twin: OK"
    )

except Exception as e:
    logger.error(
        f"Digital Twin błąd: {e}"
    )

    results["digital_twin"] = {
        "status": "ERROR",
        "error": str(e)
    }

# ============================================================
# LONGITUDINAL MODEL
# ============================================================

logger.info("")
logger.info("========== LONGITUDINAL ANALYSIS ==========")

try:
    longitudinal_module = safe_import(
        "models.longitudinal_model"
    )

    if longitudinal_module and hasattr(
        longitudinal_module,
        "LongitudinalModel"
    ):
        longitudinal_model = longitudinal_module.LongitudinalModel(
            config=config
        )

        longitudinal_result = longitudinal_model.update(
            results
        )

    elif longitudinal_module and hasattr(
        longitudinal_module,
        "analyze"
    ):
        longitudinal_result = longitudinal_module.analyze(
            results,
            config
        )

    else:
        longitudinal_result = {
            "status": "NOT_IMPLEMENTED"
        }

    results["digital_twin"]["longitudinal"] = longitudinal_result

    logger.info(
        "Longitudinal analysis: OK"
    )

except Exception as e:
    logger.error(
        f"Longitudinal błąd: {e}"
    )

# ============================================================
# DECISION ENGINE
# ============================================================

logger.info("")
logger.info("========== DECISION ENGINE ==========")

try:
    decision_module = safe_import(
        "decision.decision_engine"
    )

    if decision_module and hasattr(
        decision_module,
        "DecisionEngine"
    ):
        decision_engine = decision_module.DecisionEngine(
            config=config
        )

        decision_result = decision_engine.evaluate(
            results
        )

    elif decision_module and hasattr(
        decision_module,
        "evaluate"
    ):
        decision_result = decision_module.evaluate(
            results,
            config
        )

    else:
        decision_result = {
            "status": "NOT_IMPLEMENTED"
        }

    results["decision"] = decision_result

    logger.info(
        "Decision engine: OK"
    )

except Exception as e:
    logger.error(
        f"Decision engine błąd: {e}"
    )

    results["decision"] = {
        "status": "ERROR",
        "error": str(e)
    }

# ============================================================
# ZAPIS WYNIKÓW
# ============================================================

save_json(
    results,
    "analysis_result.json"
)

# ============================================================
# PODSUMOWANIE
# ============================================================

logger.info("")
logger.info("=" * 70)
logger.info("PODSUMOWANIE SYSTEMU")
logger.info("=" * 70)

logger.info(
    f"SAM2: {results['image']['sam2'].get('status', 'OK')}"
)

logger.info(
    f"Cellpose: {results['cells']['cellpose'].get('status', 'OK')}"
)

logger.info(
    f"MONAI: {results['image']['monai'].get('status', 'OK')}"
)

logger.info(
    f"DINOv2: {results['image']['dinov2'].get('status', 'OK')}"
)

logger.info(
    f"Scanpy: {results['rna'].get('status', 'OK')}"
)

logger.info(
    f"Hand: {results['hand'].get('status', 'OK')}"
)

logger.info(
    f"Fusion: {results['fusion'].get('status', 'OK')}"
)

logger.info(
    f"Aging: {results['aging'].get('status', 'OK')}"
)

logger.info(
    f"Abnormality: {results['abnormality'].get('status', 'OK')}"
)

logger.info(
    f"Pathology: {results['pathology'].get('status', 'OK')}"
)

logger.info(
    f"Risk: {results['risk'].get('status', 'OK')}"
)

logger.info(
    f"Intervention: {results['intervention'].get('status', 'OK')}"
)

logger.info(
    f"Digital Twin: {results['digital_twin'].get('status', 'OK')}"
)

logger.info(
    f"Decision: {results['decision'].get('status', 'OK')}"
)

logger.info("=" * 70)
logger.info("ANALIZA ZAKOŃCZONA")
logger.info("=" * 70)

