# Spatial evidence visual integrity — etapy 5–7

## Etap 5 — kontrola jakości materiału wielowidokowego

Sprawdzamy, czy zdjęcia przypisane do bieżącego `spatial_id` mają różne widoki i zostały przygotowane. Diagnostyka nie zmienia danych.

Kontrole:
- minimum 2 przygotowane widoki,
- liczba unikalnych widoków,
- brak podwójnego przypisania tego samego widoku,
- lista brakujących widoków.

## Etap 6 — integralność projekcji

Sprawdzamy zgodność planu projekcji, celu przestrzennego i faktycznie nałożonych warstw w scenie 3D.

Kontrole:
- zgodność `spatial_id`,
- obecność planu projekcji,
- liczba zarejestrowanych widoków,
- liczba widoków faktycznie zastosowanych na modelu.

## Etap 7 — integralność pakietu bliźniaka

Końcowy status jest pozytywny dopiero, gdy etapy 5 i 6 są spełnione, pakiet powierzchni istnieje, a wszystkie elementy wskazują ten sam cel przestrzenny.

Wynik pozostaje wizualizacją badawczą. Nie jest to automatyczne wnioskowanie anatomiczne ani diagnostyczne.

## Diagnostyka w konsoli

Po załadowaniu strony dostępne jest:

`window.testhpSpatialVisualIntegrity.run()`

oraz:

`window.testhpSpatialVisualIntegrity.getDiagnostics()`
