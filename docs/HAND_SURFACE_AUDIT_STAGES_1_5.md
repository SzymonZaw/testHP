# HAND SURFACE — audyt etapów 1–5

## Zakres

Audyt wykonano na `work/next-twin` dla modułu HAND SURFACE oraz jego połączeń z:

- MODEL PRZESTRZENNY
- INSPEKTOR CELU PRZESTRZENNEGO
- NAWIGACJA PRZESTRZENNA
- INTERPRETACJA BADAWCZA

## Etap 1 — stan obecny

HAND SURFACE jest składany dynamicznie przez `hand-surface-stages-11-15.js`, `hand-surface-edit-bridge.js` i `hand-surface-stages-20-22.js`. `hand-surface-simple-ui.js` scala te warstwy do jednego interfejsu.

Aktualny model funkcjonalny ma dwa poziomy:

1. **Materiał** — Źródła, Przygotowanie, Geometria.
2. **Rejestracja** — Kontrola jakości, Plan projekcji, Pakiet bliźniaka.

To jest właściwy podział odpowiedzialności: najpierw przygotowujemy materiał, potem sprawdzamy/rejestrujemy go i dopiero na końcu oceniamy gotowość pakietu.

### Zidentyfikowane źródła funkcji

- `hand-surface-engine.js` — wizualna powierzchnia dłoni, fallback proceduralny, kontekst przestrzenny.
- `hand-surface-stages-11-15.js` — dane obserwacyjne, przygotowanie zdjęcia, geometria proceduralna, mapowanie i workflow.
- `hand-surface-stages-20-22.js` — kontrakt geometrii i status pakietu bliźniaka.
- `hand-surface-photo-reconstruction.js` — opcjonalna rekonstrukcja ze zdjęć.
- `hand-surface-simple-ui.js` — warstwa prezentacyjna, która grupuje wcześniejsze funkcje.
- `hand-surface-debug.js` / `hand-surface-integration-debug.js` — diagnostyka, nie podstawowa funkcja użytkowa.

## Etap 2 — mapa odpowiedzialności

| Obszar | Wejście | Przetwarzanie | Wynik |
|---|---|---|---|
| Źródła | zdjęcia/obserwacje | przypisanie do aktualnego celu | rekord evidence |
| Przygotowanie | zdjęcie | separacja tła, crop, resize | prepared image |
| Geometria | parametry powierzchni | deformacja proceduralnego modelu | wizualna geometria |
| Kontrola jakości | prepared/registered views | sprawdzenie kompletności i jakości | status rejestracji |
| Plan projekcji | zarejestrowane widoki + geometria | wybór/projekcja powierzchni | plan projekcji |
| Pakiet bliźniaka | rejestracja + geometria + plan | walidacja warunków końcowych | gotowy/niegotowy |

### Granice modułów

**MODEL PRZESTRZENNY** pozostaje właścicielem widoku 3D i kontekstu przestrzennego. HAND SURFACE nie powinien tworzyć drugiego modelu nawigacyjnego.

**INSPEKTOR CELU PRZESTRZENNEGO** pozostaje właścicielem informacji o aktualnym celu biologicznym. HAND SURFACE korzysta z tego celu.

**NAWIGACJA PRZESTRZENNA** pozostaje źródłem prawdy dla ścieżki i `spatial_id`. HAND SURFACE nie powinien zastępować nawigacji własnym drzewem.

**INTERPRETACJA BADAWCZA** pozostaje właścicielem interpretacji biologicznej. HAND SURFACE dostarcza materiał/evidence, a nie diagnozę.

## Etap 3 — duplikaty i diagnostyka

Zidentyfikowano trzy grupy treści:

### Zostawić w HAND SURFACE

- przygotowanie zdjęć,
- parametry geometrii powierzchni,
- rejestracja widoków,
- plan projekcji,
- status gotowości pakietu.

### Nie dublować

- aktualnego celu przestrzennego,
- ścieżki nawigacji,
- danych biologicznych z Inspektora,
- interpretacji biologicznej.

Te dane są tylko kontekstem w HAND SURFACE.

### Diagnostyka

`hand-surface-debug.js` oraz `hand-surface-integration-debug.js` powinny pozostać warstwą diagnostyczną, a nie częścią głównego workflow użytkownika.

## Etap 4 — decyzja dotycząca nawigacji

Docelowa prezentacja ma **dwa główne kroki**, a nie siedem równorzędnych zakładek:

**Materiał → Rejestracja**

Wewnątrz:

**Materiał:** Źródła → Przygotowanie → Geometria

**Rejestracja:** Kontrola jakości → Plan projekcji → Pakiet bliźniaka

Kolejność jest celowa: użytkownik najpierw dostarcza i przygotowuje materiał, następnie przechodzi do rejestracji i dopiero na końcu otrzymuje status pakietu.

## Etap 5 — Materiał

Sekcja Materiał jest odpowiedzialna wyłącznie za wejście i przygotowanie:

1. **Źródła** — jakie obserwacje są przypisane do bieżącego celu.
2. **Przygotowanie** — przygotowanie obrazu bez zmiany oryginału.
3. **Geometria** — dopasowanie proceduralnej powierzchni jako wizualnego/fallbackowego modelu.

Ważna granica: geometria proceduralna nie jest dowodem rejestracji fotograficznej i nie może sama oznaczać pakietu jako gotowego.

## Wniosek po etapach 1–5

Architektura funkcjonalna jest zasadniczo poprawna. Największy problem był prezentacyjny: wiele starszych paneli jest tworzonych osobno, a następnie ukrywanych i składanych przez `hand-surface-simple-ui.js`. Dlatego uproszczenie powinno dotyczyć przede wszystkim warstwy prezentacyjnej, bez usuwania działających kontraktów danych.

Etapy 1–5 nie wymagają usuwania mechanizmów backendowych ani diagnostycznych. Kolejne etapy powinny skupić się na rzeczywistym zachowaniu zakładek Rejestracja, szczególnie Kontroli jakości, Planu projekcji i Pakietu bliźniaka.
