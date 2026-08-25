# Dopasowanie geometrii dłoni — etapy 1–4

Branch: `feature/spatial-evidence-visual-integrity`

## Cel

Przejście od pomiarów rzeczywistej dłoni do istniejącej geometrii 3D bez zmiany ani usuwania evidence.

### 1. Zdjęcia

Zbieramy pięć kontrolowanych widoków: `front`, `back`, `side_left`, `side_right`, `thumb`. Dłoń powinna pozostać nieruchoma, a aparat możliwie prostopadły do fotografowanej powierzchni. Wzorzec długości powinien leżeć w tej samej płaszczyźnie co dłoń.

### 2. Skala

Wprowadzamy znaną długość wzorca w mm oraz jego długość w pikselach. Pozwala to zachować informację o skali sesji. Jeżeli skali nie ma, etap 4 nadal może działać proporcjami, ale wynik jest oznaczony jako `proportion-only`.

### 3. Pomiary

W UI można podać długość, szerokość i grubość dłoni oraz długości palców i kąt kciuka. Wartości są przechowywane lokalnie w przeglądarce.

### 4. Dopasowanie

Pomiary są deterministycznie mapowane na istniejące parametry `hand-geometry-permanent-module.js`: `palmLength`, `palmWidth`, `thickness`, `fingerSpread`, `taper`, `thumbAngle`. Przycisk „Zastosuj do modelu 3D” wywołuje istniejące API geometrii.

## Ważne ograniczenie

To jest pierwszy etap pomiarowo-wizualny, a nie pełna fotogrametria. Nie tworzy jeszcze siatki 3D z wielu zdjęć ani nie estymuje automatycznie 3D landmarków. Następny krok powinien zastąpić ręczne pomiary automatycznym landmarkingiem / rekonstrukcją wielowidokową, zachowując ten sam kontrakt parametrów modelu.
