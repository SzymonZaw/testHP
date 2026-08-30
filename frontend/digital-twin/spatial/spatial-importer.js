import { createCoordinateSystem, createSpatialAsset, createSpatialSource } from "./spatial-types.js";
import { validateCoordinateSystem, validateSpatialAsset, validateSpatialSource } from "./spatial-validator.js";

const SUPPORTED_FORMATS = new Set([".glb", ".gltf"]);

function extensionOf(name = "") {
  const index = name.lastIndexOf(".");
  return index >= 0 ? name.slice(index).toLowerCase() : "";
}

export function validateSpatialImportInput({ assetFile, metadata, regions }) {
  const errors = [];
  if (!assetFile?.name) errors.push("A .glb or .gltf asset file is required.");
  const extension = extensionOf(assetFile?.name);
  if (assetFile?.name && !SUPPORTED_FORMATS.has(extension)) {
    errors.push(`Unsupported asset format: ${extension || "unknown"}. Use .glb or .gltf.`);
  }
  if (!metadata || typeof metadata !== "object") errors.push("Metadata object is required.");
  if (!Array.isArray(regions)) errors.push("regions must be an array.");
  return { valid: errors.length === 0, errors };
}

export async function importSpatialAsset({ assetFile, metadata, regions, evidence = [], gltfLoader }) {
  const inputValidation = validateSpatialImportInput({ assetFile, metadata, regions });
  if (!inputValidation.valid) throw new Error(inputValidation.errors.join(" "));
  if (!gltfLoader || typeof gltfLoader.load !== "function") {
    throw new Error("A GLTFLoader-compatible loader must be supplied by the application.");
  }

  const source = createSpatialSource(metadata.source || {
    id: metadata.sourceId || `upload:${assetFile.name}`,
    type: "own_dataset",
    label: "Uploaded spatial dataset",
  });
  const coordinateSystem = createCoordinateSystem(metadata.coordinateSystem || {});
  const asset = createSpatialAsset({
    id: metadata.assetId || `asset:${assetFile.name}`,
    version: metadata.assetVersion || "1.0.0",
    format: extensionOf(assetFile.name).slice(1),
    sourceId: source.id,
    assetUrl: metadata.assetUrl,
    coordinateSystemId: coordinateSystem.id,
    regions,
    metadata,
  });

  const validation = {
    source: validateSpatialSource(source),
    coordinateSystem: validateCoordinateSystem(coordinateSystem),
    asset: validateSpatialAsset(asset),
  };
  if (!validation.source.valid || !validation.coordinateSystem.valid || !validation.asset.valid) {
    const errors = [...validation.source.errors, ...validation.coordinateSystem.errors, ...validation.asset.errors];
    throw new Error(`Spatial dataset validation failed: ${errors.join(" ")}`);
  }

  const objectUrl = URL.createObjectURL(assetFile);
  try {
    const gltf = await new Promise((resolve, reject) => {
      gltfLoader.load(objectUrl, resolve, undefined, reject);
    });
    return { source, coordinateSystem, asset, evidence, gltf, validation };
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}
