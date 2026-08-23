# Phase A — spójność kontekstu przestrzennego

## Kontrakt

- UI-owa nazwa regionu: **Śródręcze**.
- Canonical ID: `hand/palm`.
- Alias `Palm`, `palm`, `Śródręcze` i `srodrecze` normalizuje się do `hand/palm`.
- Jeden aktywny `spatial_id` jest publikowany do managera viewportu, obserwacji i evidence.
- Dane bezpośrednie są domyślnym zakresem regionu.
- Dane potomne są opcjonalne i muszą być jawnie włączone przez `include_descendants`.
- Dane z rodzeństwa i innych regionów nigdy nie są częścią zakresu.

## Kryterium ukończenia

Przejście `Śródręcze → obserwacje → zdjęcia/powierzchnia 3D → stan biologiczny → powrót` musi zachowywać `hand/palm` jako jeden canonical kontekst.

Regresje dla zakresu i canonicalizacji są w `tests/test_phase_a_context.py`.
