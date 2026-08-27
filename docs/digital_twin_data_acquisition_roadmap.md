# Digital Twin dłoni — roadmap danych i pozyskiwania

## Cel

System ma docelowo łączyć dane o tej samej dłoni i tym samym czasie badania na kilku skalach: fotografia i geometria 3D → anatomia/tkanki → histologia → komórki → omiki. Każdy wynik musi mieć pochodzenie, jakość, układ współrzędnych oraz identyfikator podmiotu i punktu czasowego.

To jest roadmapa **pozyskania danych**, a nie deklaracja, że model już potrafi diagnozować chorobę, określać wiek komórki lub rekomendować terapię. Te zastosowania wymagają osobnych badań walidacyjnych i klinicznych.

## Zasada nadrzędna: jeden identyfikator, wiele skal

Każdy rekord powinien być możliwy do powiązania przez:

- `subject_id` — pseudonimizowany identyfikator osoby;
- `hand_id` — konkretna dłoń (lewa/prawa);
- `timepoint_id` — moment badania;
- `acquisition_id` — konkretna sesja pozyskania;
- `asset_id` — konkretny plik lub obiekt danych;
- `spatial_reference` — układ współrzędnych i transformacja;
- `provenance` — kto/co/kiedy/jak wytworzyło dane;
- `quality` — parametry jakości i status walidacji.

Nie wolno łączyć danych z różnych osób tylko dlatego, że wyglądają podobnie. Jeśli wspólny identyfikator nie istnieje, relacja ma być oznaczona jako brakująca, a nie zgadywana.

## Etapy realizacji

### Etap 1 — kontrakt danych

Zdefiniować słownik pól, wersjonowanie schematów, identyfikatory oraz minimalne metadane dla każdego typu danych.

**Dane:** JSON/JSONL + metadane tabelaryczne; później warstwa obiektowa dla dużych plików.

**Gotowe, gdy:** każdy asset ma subject/hand/timepoint, provenance, quality i jednoznaczny typ źródła.

### Etap 2 — kohorta referencyjna

Zbudować małą, kontrolowaną kohortę badawczą. Na tym etapie ważniejsza jest jakość i kompletność metadanych niż liczba osób.

Dla każdej osoby zbierać zgodę, podstawowe dane demograficzne, dominującą rękę, historię sesji i kryteria wykluczenia. Dane osobowe przechowywać poza warstwą analityczną i używać pseudonimów.

### Etap 3 — fotografia dłoni

Pozyskiwać standaryzowane widoki: `front`, `back`, `side_left`, `side_right`, `thumb` oraz opcjonalne dodatkowe ujęcia.

**Sprzęt:** stała kamera/smartfon, statyw, kontrolowane światło, neutralne tło, marker skali albo wzorzec kalibracyjny.

**Dane:** JPEG/PNG/TIFF + EXIF/metadata + kalibracja kamery + skala + orientacja.

**Metadane:** ogniskowa, rozdzielczość, czas, ekspozycja, odległość, ustawienie kamery, wersja protokołu.

### Etap 4 — geometria 2D/3D

Z fotografii wyznaczać landmarki, maskę dłoni, kontur, powierzchnię oraz — gdy liczba i geometria ujęć na to pozwalają — rekonstrukcję 3D.

**Dane:** punkty/landmarki, maski segmentacji, mesh, point cloud, mapa głębi, transformacje.

**Ważne:** przechowywać błąd rekonstrukcji i informację o tym, które powierzchnie są rzeczywiście obserwowane, a które są estymowane.

### Etap 5 — anatomia i obrazowanie medyczne

Dla podzbioru kohorty pozyskiwać dane kliniczne/imagingowe zgodnie z protokołem badawczym: MRI, US lub inne odpowiednie modalności.

**Dane:** DICOM + segmentacje + adnotacje struktur + parametry badania.

**Cel:** powiązać powierzchnię dłoni z układem anatomicznym, nie zastępować obrazu medycznego samą fotografią.

### Etap 6 — rejestracja multimodalna

Zdefiniować transformacje między fotografią/3D a obrazowaniem medycznym. Każda transformacja musi mieć wersję, metodę i miarę błędu.

**Dane:** macierze transformacji, landmark pairs, registration metrics, maski obszarów ważności.

### Etap 7 — tkanki i histologia

Pozyskiwać materiał tkankowy wyłącznie w ramach odpowiedniego badania/biobanku i zgodnie z etyką. Łączyć preparat z dokładnym miejscem pobrania i czasem.

**Dane:** whole-slide images (np. SVS/NDPI/TIFF), mikroskopia, stain/protokół, orientacja, blok/sekcja, adnotacje patologiczne.

### Etap 8 — segmentacja tkanek i patologia

Eksperci oznaczają typy tkanek i zmiany patologiczne. Model może później uczyć się na tych etykietach, ale etykieta musi mieć źródło i status eksperta.

**Dane:** maski wieloklasowe, poligony, bounding boxes, diagnozy/grade, confidence, annotator_id.

### Etap 9 — komórki

Na odpowiednio wysokiej rozdzielczości wykonywać segmentację pojedynczych komórek.

**Dane:** centroidy, kontury/maski, cechy morfologiczne, typ komórki, jakość segmentacji.

**Minimalne cechy:** rozmiar, pole, obwód, wydłużenie, okrągłość, jądro/cytoplazma, pozycja przestrzenna.

### Etap 10 — identyfikacja i stan komórek

Identyfikować typy komórek oraz definiować stan biologiczny wyłącznie na podstawie zwalidowanych markerów i/lub modeli.

**Dane:** markery immunohistochemiczne/immunofluorescencyjne, obrazy wielokanałowe, adnotacje ekspertów, klasy stanu i confidence.

Nie używać etykiety `healthy/diseased` jako prawdy bez określonego protokołu referencyjnego.

### Etap 11 — genomika i transkryptomika

Dla próbek powiązanych z tkanką/obszarem pozyskiwać scRNA-seq i, gdy dostępne, spatial transcriptomics.

**Dane:** FASTQ/BAM, count matrices, H5AD/AnnData, gene annotations, QC metrics, spatial spots/cells.

### Etap 12 — proteomika i epigenetyka

Dodawać proteomikę oraz pomiary epigenetyczne dla tych samych próbek lub jawnie oznaczać brak bezpośredniego sparowania.

**Dane:** intensywności/abundance, identyfikatory białek/peptydów, methylation/ATAC/chromatin features, batch i QC.

### Etap 13 — integracja multi-omics

Normalizować i integrować modalności z zachowaniem informacji o batchach, platformie, próbce i jakości. Nigdy nie usuwać informacji o źródle przy agregacji.

**Wynik:** wspólny obiekt analityczny z linkami do źródłowych assetów.

### Etap 14 — longitudinal

Powtarzać te same protokoły u tych samych osób. Minimum to wiele punktów czasowych z kontrolą zmian sprzętu/protokołu.

**Dane:** serie pomiarów + delta/trajectory features + wersja protokołu + warunki akwizycji.

To jest fundament do badania trajektorii starzenia; pojedynczy pomiar nie daje trajektorii.

### Etap 15 — modele wieku biologicznego i stanu

Dopiero po zgromadzeniu odpowiedniej kohorty i niezależnych etykiet budować modele wieku biologicznego, zdrowia/choroby i ryzyka.

Model powinien zwracać wynik + przedział niepewności + źródła danych + ograniczenia. Nie powinien zwracać pozornej pewności na podstawie brakujących modalności.

### Etap 16 — unified spatial model

Zbudować hierarchię: dłoń → region → struktura → tkanka → komórka → cecha molekularna. Każdy poziom musi mieć referencję przestrzenną i link do poziomu nadrzędnego.

### Etap 17 — what-if, ryzyko i interwencje

Dopiero po walidacji modeli można tworzyć symulacje zmian i system wspierający decyzje. Na tym etapie wynik powinien być oznaczony jako badawczy, a nie jako automatyczna rekomendacja leczenia.

### Etap 18 — walidacja i ścieżka kliniczna

Wprowadzić niezależny test set, walidację zewnętrzną, analizę błędów i biasu, test-retest, drift danych oraz audyt pochodzenia. Jeśli system ma kiedyś wpływać na decyzje kliniczne, zaplanować odpowiednią ścieżkę regulacyjną i bezpieczeństwo danych.

## Jakie dane zbierać — skrót

| Skala | Źródło | Główne dane | Format/przykład | Powiązanie |
|---|---|---|---|---|
| Makro | zdjęcia | obrazy, EXIF, kalibracja | JPG/PNG/TIFF | subject/hand/timepoint |
| 3D | fotogrametria/depth | mesh, point cloud, depth | PLY/OBJ/GLB/NPY | acquisition + spatial ref |
| Anatomia | MRI/US | obrazy, serie, segmentacje | DICOM/NIfTI | study/series/space |
| Tkanka | histologia/WSI | slajdy, stain, adnotacje | SVS/NDPI/TIFF | specimen/section |
| Komórka | mikroskopia | maski, centroidy, cechy | OME-TIFF + tables | cell_id + spatial ref |
| RNA | scRNA/spatial | counts, genes, spots/cells | H5AD/MTX/TSV/FASTQ | sample + region |
| Białka | proteomika | abundance/markers | tabular/raw vendor | sample |
| Epigenetyka | ATAC/methylation | peaks/methylation | BED/MTX/H5AD | sample |
| Czas | longitudinal | serie i delty | metadata + feature tables | subject + timepoint |

## Kolejność pozyskiwania w praktyce

1. Najpierw dopracować **metadata + provenance + quality**.
2. Następnie zebrać mały, bardzo dobrze opisany zestaw fotografii dłoni.
3. Dodać kalibrację i geometrię 3D.
4. Dopiero potem dołączyć MRI/US dla części kohorty.
5. Następnie próbki histologiczne i WSI dla podzbioru.
6. Na tych samych/ściśle powiązanych próbkach dodać dane komórkowe.
7. Dołożyć omiki.
8. Powtarzać pomiary w czasie.
9. Dopiero wtedy trenować modele wieku/stanu/ryzyka.
10. Po niezależnej walidacji rozważać zastosowania kliniczne.

## Czego nie robić

- Nie generować brakujących pomiarów jako „danych rzeczywistych”.
- Nie łączyć osoby, próbki lub punktu czasowego po podobieństwie obrazu.
- Nie nazywać predykcji „diagnozą” bez walidacji klinicznej.
- Nie wyznaczać „wieku komórki” z samego wyglądu bez odpowiedniego ground truth.
- Nie mieszać danych treningowych i testowych z tej samej osoby bez kontroli leakage.
- Nie usuwać provenance przy normalizacji.
- Nie traktować rekonstrukcji 3D jako bezbłędnego pomiaru — przechowywać niepewność.

## Definition of Done dla całego pipeline'u

Projekt jest gotowy do pierwszego poważnego eksperymentu modelowego dopiero wtedy, gdy dla reprezentatywnego podzbioru istnieją: kompletne identyfikatory, fotografia, geometria, przynajmniej jedna niezależna modalność anatomiczna, zwalidowane adnotacje tkankowe/komórkowe, QC, provenance, powiązanie przestrzenne oraz co najmniej dwa punkty czasowe dla części longitudinalnej.
