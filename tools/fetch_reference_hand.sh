#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-frontend/digital-twin/reference-data}"
mkdir -p "$ROOT"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

URL="https://github.com/HegdeUSA/Hand_template/raw/refs/heads/main/3D_model_of_hand_template.zip"
ZIP="$TMP/hand-template.zip"

echo "Fetching NIH/Hegde healthy adult hand template..."
curl -L --fail --retry 3 "$URL" -o "$ZIP"
unzip -o "$ZIP" -d "$ROOT"

echo
echo "Reference fetched into: $ROOT"
echo "Source: https://3d.nih.gov/entries/3DPX-017237"
echo "Do not treat this template as a patient-specific hand."
echo "Do not invent palm/thumb/index/... geometry IDs; supply a real segmentation/annotation manifest first."
