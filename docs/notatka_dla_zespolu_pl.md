# Notatka techniczna — start projektu

Cel projektu: artykuł naukowy o tym, **ile danych z urządzeń ubieralnych** (zegarki Fitbit, glukometry CGM, pasek pomiarowy hormonów Mira) **wystarczy, żeby wiarygodnie przewidzieć fazę cyklu menstruacyjnego**. Zbiór danych: mcPHASES (publiczny, PhysioNet) — 42 uczestniczki, dwie tury pomiarowe (2022 i 2024).

Pierwszy termin: **konferencja studencka 7 maja**. Wymagany rezultat: jeden wykres, jedna tabela, krótki tekst (poster lub artykuł 4 strony).

Dokument zawiera: (1) opis metody, (2) inwentarz repozytorium, (3) ścieżkę startu, (4) przydziały zadań per rola, (5) zakres na 7 maja, (6) typowe problemy.

---

## 1. Metoda

Klasyczne podejście: trenujemy klasyfikator binarny (przed owulacją / po owulacji), dla każdej (uczestniczka, noc) zwracamy jedną etykietę.

Nasze podejście: zamiast jednej etykiety zwracamy **zbiór możliwych etykiet** o gwarantowanym pokryciu probabilistycznym. Dla problemu binarnego zbiór ma rozmiar 1 lub 2:
- rozmiar 1 — model jest pewny, zwracamy predykcję,
- rozmiar 2 — model nie jest pewny, decyzja: *odroczyć* lub *zebrać więcej danych*.

**Próg wystarczalności** τᵢ — najmniejsza liczba ważnych nocy k, dla której zbiór predykcyjny dla i-tej uczestniczki ma rozmiar 1 dla co najmniej dwóch kolejnych okien obserwacyjnych. Hipoteza badawcza: τᵢ jest zmienne w populacji i daje się przewidzieć z obserwowalnych zmiennych towarzyszących (kompletność sygnału, regularność cyklu, dostępne modalności).

Metoda statystyczna: **conformal prediction** w wariancie **Adaptive Prediction Sets (APS)** zaproponowanym w Romano et al. 2020. Walidacja: leave-one-subject-out cross-validation (LOSO-CV) na 5-fold grouped CV w wersji awaryjnej.

Literatura wprowadzająca: Angelopoulos & Bates 2021 (arXiv:2107.07511), sekcje 1–3. Pełny opis metodologiczny w `research_plan_v4.pdf` sekcje 2.3, 2.4, 3.3, 3.4.

---

## 2. Inwentarz repozytorium

### Dane

| Folder | Zawartość |
|---|---|
| `dataset/` | Surowe pliki CSV mcPHASES. Pliki małe (<10 MB) zostają w CSV. |
| `dataset_parquet/` | 9 dużych plików (heart_rate.csv 1.9 GB, calories 600 MB itd.) skonwertowanych do parquet. Konwersja: `python scripts/convert_raw_to_parquet.py`. |

Format parquet jest wymagany dla dużych plików, ponieważ surowy `heart_rate.csv` nie mieści się w pamięci darmowego Colaba.

### Biblioteka wczytywania

`utils/dataset.py` — ujednolicony loader. Standardowe wywołanie:

```python
from utils.dataset import setup, load_mcphases

setup()                 # podpina Drive na Colabie; no-op lokalnie
data = load_mcphases()  # auto-detekcja ścieżki

hormones = data['hormones_and_selfreport']     # mała tabela, eager
hr_p18 = data.load('heart_rate', participant_id=18, columns=['day_in_study', 'bpm'])  # duża, lazy
```

Loader normalizuje nazwy kolumn (lowercase, `id` → `participant_id`) zgodnie z kontraktem danych.

### Notebooki

| Plik | Funkcja |
|---|---|
| `notebooks/00_getting_started.ipynb` | Wprowadzenie do środowiska |
| `notebooks/06_dataset_loading.ipynb` | Tutorial loadera, w tym migracja z `pd.read_csv` |
| `notebooks/01_wp2_preprocessing.ipynb` | Przygotowanie danych: kohortę, valid_nights, missingness, LOSO folds |
| `notebooks/02_wp3_endpoint.ipynb` | Konstrukcja etykiety binarnej (przed/po owulacji) z hormonów |
| `notebooks/03_wp5_baselines.ipynb` | Klasyfikator bazowy + metody odniesienia (Fixed-3/5/7, always_predict) |
| `notebooks/04_wp6_conformal.ipynb` | Predykcja konformalna z APS, krzywe wystarczalności, hero figure |
| `notebooks/05_wp7_evaluation.ipynb` | Metryki, bootstrap CI, reliability diagram |

Wszystkie notebooki działają end-to-end na danych syntetycznych (`synthetic/v1/`). Każdy notebook ma sekcje markdown z opisem zadania.

### Dokumentacja

| Plik | Zawartość |
|---|---|
| `docs/data_contract_v1.md` | Schemy trzech głównych plików parquet (probability_table, labels, covariates) |
| `docs/pipeline_contract_v1.md` | Pełny przepływ danych: WP2 → WP3 → WP5 → WP6 → WP7 |
| `docs/student3_charter.md` | Specyfikacja roli „predykcja konformalna" |
| `docs/claims_boundary.md` | Granice twierdzeń artykułu |
| `docs/gap_statement.md` | Luka w literaturze + audyt cytowań |
| `docs/hero_figure_spec.md` | Specyfikacja Figure 1 (trzy panele) |
| `research_plan_v4.pdf` | Pełny plan badań |
| `docs/s44294-025-00078-8.pdf` | Kilungeja et al. 2025 — bezpośredni konkurent (różny zbiór danych, bez modelowania niepewności) |

---

## 3. Procedura startu

1. Sklonować repo lokalnie lub otworzyć na Colabie.
2. Uruchomić `notebooks/00_getting_started.ipynb`. Po wykonaniu wszystkich komórek znana jest struktura repozytorium.
3. Uruchomić `notebooks/06_dataset_loading.ipynb`. Po wykonaniu znana jest składnia loadera i schemat dostępu do tabel.
4. Uruchomić notebook odpowiadający przydzielonej roli (lista w sekcji 4). Po wykonaniu znany jest pełny pipeline na danych syntetycznych.

Czas wykonania: ok. 2 godziny.

---

## 4. Zadania per rola

### Predykcja konformalna

Notebook bazowy: `04_wp6_conformal.ipynb`. Działa end-to-end na danych syntetycznych z LOSO + per-k kalibracją + APS + fallbackiem na argmax dla pustych zbiorów.

Harmonogram do 7 maja:

| Dzień | Zadanie | Wynik |
|---|---|---|
| 1 | Lektura: plan §2.3, §2.4, §3.3, §3.4. Angelopoulos & Bates §1–3. Uruchomienie notebooków 04 i 06. | — |
| 2 | Detektor skoku LH na `data['hormones_and_selfreport']` (lokalne maksimum > 10 mIU/mL). | `synthetic/v1/labels.parquet` (n=19, R2) |
| 3 | Klasyfikator bazowy: regresja logistyczna na średniej nocnej temperaturze skóry, kalibracja izotoniczna. | `probability_table.parquet` |
| 4 | Notebook 04 na prawdziwych danych. Pierwszy wykres |C_α| vs k. | Wykres + plik `prediction_sets.parquet` |
| 5 | Iteracja, obsługa edge cases (braki nocy, dziwne rozkłady). | — |
| 6 | Tabela porównawcza: nasza metoda vs Fixed-5. Bootstrap CI 2 000 iteracji. | Tabela |
| 7 | Sekcja Methods + Results. | — |
| 8 | Sekcja Introduction + Discussion + Limitations. Polerka wykresu. | — |
| 9 | Konferencja. | — |

Zakres awaryjny: punkty 2 i 3 (etykiety i klasyfikator) są stand-inami. Jeśli osoby od WP2/WP3 i WP5 dostarczą swoje wersje wcześniej — następuje podmiana ścieżek wejściowych, kod nie wymaga zmian.

Poza zakresem konferencji (do wersji pełnej): stratyfikacja Mondriana, model regresji predykujący τᵢ, analiza longitudinalna R1→R2.

### Przygotowanie danych i etykiet

Notebooki bazowe: `01_wp2_preprocessing.ipynb`, `02_wp3_endpoint.ipynb`.

Zadania na 7 maja:

1. Zdefiniowanie operacyjne „ważnej nocy". Propozycja z planu §4.3: ≥4 godziny ciągłego snu w oknie 22:00–06:00. Plik wyjściowy: `preprocessing/valid_nights.parquet`.
2. Kohortę dla podzbioru 19 uczestniczek z drugiej rundy (study_interval=2024). Plik: `preprocessing/cohort.parquet`.
3. Etykietę binarną z hormonów: skok LH + potwierdzenie wzrostem PdG przez ≥2 dni. Plik: `labels.parquet`. Parametry detektora i progu PdG do uzgodnienia z opiekunem.
4. Migracja własnego notebooka `notebooks_from_students/mcPHASES_preprocessing.ipynb` na loader (`utils.dataset.load_mcphases`) — eliminuje ~50 linii kodu wczytującego CSV. Tutorial w `notebooks/06_dataset_loading.ipynb` sekcja 5.

Schematy plików wyjściowych: `docs/pipeline_contract_v1.md` sekcje 3 i 4.

### Klasyfikator bazowy i metody odniesienia

Notebook bazowy: `03_wp5_baselines.ipynb`.

Zadania na 7 maja:

1. Ekstrakcja cech z `dataset_parquet/`: średnia i odchylenie standardowe nocnej temperatury skóry (`computed_temperature` lub agregacja `wrist_temperature` na noc), średnie HR i HRV (`heart_rate`, `heart_rate_variability_details`), średnia glikemia (`glucose`). Granularność: jedna liczba na (uczestniczka, noc).
2. Klasyfikator: LightGBM lub regresja logistyczna z kalibracją izotoniczną (`sklearn.isotonic.IsotonicRegression`). Walidacja: 5-fold grouped CV (uczestniczki w grupach).
3. Plik wyjściowy: `probability_table.parquet` z prawdopodobieństwem klasy „post" dla każdej (uczestniczka, noc).
4. Implementacja jednej metody odniesienia: **Fixed-5**. Plik: `decisions/fixed_5.parquet`.

Poza zakresem konferencji: Oracle global threshold, signal-quality heuristic, Fixed-3 i Fixed-7.

### Statystyka i ewaluacja

Notebook bazowy: `05_wp7_evaluation.ipynb`.

Zadania na 7 maja:

1. Wczytanie `decisions/*.parquet` od osób od WP5 i WP6.
2. Metryki: median τᵢ, IQR τᵢ, selective accuracy, deferral rate.
3. Empirical coverage z `prediction_sets.parquet` — czy zbiór konformalny zawiera prawdziwą etykietę w ≥90% przypadków. Ta metryka jest centralna dla artykułu, ponieważ raportujemy *empirical coverage*, nie *formal coverage* (plan §2.4).
4. Bootstrap CI: 2 000 iteracji, BCa correction. W wersji do czasopisma 10 000.

---

## 5. Zakres na 7 maja

### Produkty wejściowe na konferencję

- 1 wykres (krzywe wystarczalności |C_α| vs k dla ~10 reprezentatywnych uczestniczek z R2)
- 1 tabela (Fixed-5 vs covariate_conditional na czterech metrykach z bootstrap CI)
- Tekst: poster lub artykuł 4 strony (do uzgodnienia z opiekunem)

### Świadomie poza zakresem (do wersji pełnej, czerwiec/lipiec)

- Pełna kohortę n=42. Wersja konferencyjna: tylko 19 uczestniczek z R2 (mają pełny panel hormonalny).
- Etykiety wielopoziomowe (gold/silver/bronze/charcoal). Wersja konferencyjna: binarne LH+PdG dla R2.
- Stratyfikacja Mondriana, model regresji dla τᵢ, longitudinal transfer R1→R2.
- Pre-rejestracja na OSF, kontener Docker, CI/CD, weryfikacja cytowań.
- Walidacja przez statystyka zewnętrznego.

### Twardy harmonogram końcowy

- 4 maja: zamrożenie zakresu wyników, koniec zmian metodologicznych.
- 5 maja: koniec analiz, początek pisania.
- 6 maja: poprawki, korekta językowa.
- 7 maja: złożenie/prezentacja.

---

## 6. Typowe problemy

| Objaw | Przyczyna | Rozwiązanie |
|---|---|---|
| Colab wywala pamięć przy `pd.read_csv('heart_rate.csv')` | Plik CSV za duży na 12 GB RAM | Uruchomić `python scripts/convert_raw_to_parquet.py`, używać `data.load(...)` z parquet |
| `load_mcphases()` rzuca `FileNotFoundError` | Dane w nietypowej lokalizacji | `load_mcphases(data_dir='/twoja/ścieżka')` |
| `ImportError: utils.dataset` w notebooku | Brak `sys.path.insert(0, REPO_ROOT)` | Komórka setup z notebooka 00 |
| `ContractViolation` z walidatora | Niezgodne typy lub kolumny | Sprawdzić schemę w `data_contract_v1.md`, użyć `df.astype({...})` przed `to_parquet` |
| `pd.read_parquet` ignoruje `filters=` | Niewystarczająco nowy pyarrow | `requirements.txt` wymaga `pyarrow>=17`; sprawdzić wersję |
