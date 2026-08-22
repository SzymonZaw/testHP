# HAND SURFACE — etapy 6–10

## Etap 6 — funkcjonalna sekcja Rejestracja

Sekcja Rejestracja ma trzy rzeczywiste podwidoki:

1. Kontrola jakości
2. Plan projekcji
3. Pakiet bliźniaka

Każdy przełącza zawartość tego samego panelu. Nie są to już wyłącznie etykiety prezentacyjne.

## Etap 7 — Kontrola jakości

Kontrola jakości pokazuje dla bieżącego `spatial_id` wszystkie pięć oczekiwanych widoków (`front`, `back`, `side_left`, `side_right`, `thumb`) oraz rozdziela:

- materiał przygotowany,
- materiał zarejestrowany.

Geometria proceduralna nie jest zaliczana jako rejestracja.

## Etap 8 — Plan projekcji

Plan jest generowany z faktycznie zarejestrowanych widoków i zapisywany jako `digitalTwinSurfaceProjection.v2`. Zawiera cel, listę widoków, pokrycie i metodę.

## Etap 9 — Pakiet bliźniaka

Status pakietu jest wynikiem jawnej walidacji:

- 5/5 widoków z rejestracją,
- geometria skalibrowana i niebędąca fallbackiem proceduralnym,
- istniejący plan projekcji dla tego samego celu.

Sam proceduralny model nigdy nie oznacza pakietu jako gotowego.

## Etap 10 — granice i regresja

HAND SURFACE nadal korzysta z istniejącego źródła `spatial_id` i nie tworzy własnej nawigacji. Diagnostyka pozostaje poza głównym workflow.

Zakładki Materiał pozostają właścicielem wejścia i przygotowania, a Rejestracja właścicielem kontroli, planu i gotowości.

### Rezultat

Podstawowy problem poprzedniego UI — kliknięcie „Kontrola jakości / Plan projekcji / Pakiet bliźniaka” bez zmiany zawartości — został usunięty przez wprowadzenie rzeczywistego przełączania i renderowania trzech podwidoków.