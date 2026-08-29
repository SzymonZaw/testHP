# Etapy 1–7 — fundament i komórkowa reprezentacja

## Kanoniczny przepływ

```text
Frontend
  ↓
Data Contract
  ↓
DigitalTwin
  ↓
Domain models
  ↓
Evidence / Provenance
```

## Hierarchia przestrzenna

```text
Hand → Structure → Region → Tissue → Microscopy → Cell
```

Każdy element przestrzenny ma `spatial_id`; relacje rodzic–dziecko są walidowane przez kontrakt DigitalTwin.

## Etap 1

`backend/foundation_contract.py` definiuje kanoniczne `DigitalTwin`, `SpatialRef`, `SpatialLevel` i `Evidence`.

CI dla brancha `dev/next-cleanup` uruchamia kompilację backendu oraz testy kontraktowe.

## Etap 2–3

`backend/hand_tissue_contract.py` definiuje układ współrzędnych, transformacje, struktury anatomiczne i regiony tkanek.

## Etap 4–7

`backend/microscopy_cell_contract.py` i `backend/cell_analysis_contract.py` definiują obrazy mikroskopowe, segmentację, instancje komórek, tożsamość komórki i ocenę typu komórki.

Wyniki modeli zawsze mogą nieść `confidence`, `evidence`/provenance oraz wersję modelu. Kontrakty nie przedstawiają niezwalidowanych wyników jako diagnozy klinicznej.

## Zasada implementacyjna

Najpierw stabilny kontrakt i provenance, następnie pipeline danych, modele ML i niezależna walidacja. Nie traktujemy przykładowych etykiet ani confidence jako rzeczywistych wyników biologicznych bez danych i walidacji.
