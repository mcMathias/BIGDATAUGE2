# 20555 – Starterprojekt: Kan vi stole på live-eldata?

## Din opgave

Du skal bygge en reproducerbar datapipeline, som sammenligner Energinets operationelle femminuttersdata med senere afregningsdata.

```text
rå JSON
→ validering
→ MW til MWh
→ timeaggregation
→ join
→ kvalitetsflag
→ analyseklart output
→ undersøgelse og faglig forklaring
```

Du skal ikke have API-adgang. Projektet indeholder faste danske datasnapshots, så alle kan arbejde på samme datagrundlag og fortsætte uden internet.

## Sådan bruges filerne

- `README.md` bruges til **teknisk opstart, filoverblik og fejlsøgning**.
- `OPGAVE.md` styrer **rækkefølgen i casearbejdet, kravene og checkpoints**. Følg kun det aktuelle modul.
- `DATAORDLISTE.md` er et **opslagsværk** til casebegreber og domænetermer; den skal ikke læses fra start til slut før arbejdet kan begynde.

Hvis du arbejder fra den samlede lærlingepakke, bruger du `20555_Laerling_Forloebsoversigt.md` til hele fagets Modul01–Modul05-progression.

## Start her

1. Åbn en terminal i denne mappe.
2. Kontrollér setup og data:

```powershell
python check_setup.py
```

3. Når du får `SETUP PASS`, går du til **det aktuelle modul i `OPGAVE.md`**.
4. Ved første opstart er det Modul01: undersøg snapshots og metadata, udfyld kildeskemaet og tegn pipelineskitsen. **TODO 1–3 implementeres først i Modul02.**

Til kildeskema og pipelineskitse i Modul01 kan du bruge `kilder_og_pipeline.md` i docs-mappen. Senere kan `undersoegelser_og_ansvar.md` støtte undersøgelserne. Skabelonerne er frivillig støtte til kravene i `OPGAVE.md`; du kan vælge en anden dokumentationsform.

## Når du kommer til Modul02

Åbn `src/pipeline.py`, og arbejd med `TODO 1–3` som beskrevet i `OPGAVE.md`. Start med den lille periode omkring sommertidsskiftet og brug Modul02-checkpointet:

```powershell
python run_pipeline.py --period dst --stage realtime
```

Efter `TODO 1–3` skriver kommandoen `realtime_hourly_dst.csv` i outputmappen uden at kræve TODO 4–6. Kommandoen dokumenterer kørsel; du skal stadig kontrollere enheder, grain og dækning.

En fuld kørsel bruges, når det aktuelle modul også omfatter de efterfølgende trin:

```powershell
python run_pipeline.py --period dst
```

Afleveringsvejledningen og Python/pandas-referencen udleveres sammen med forløbsmaterialet.

## Krav til software

- Python 3.11 eller nyere
- `pandas`

Installer projektets bibliotek, hvis det ikke allerede findes:

```powershell
python -m pip install -r requirements.txt
```

## Projektets vigtigste filer

| Fil eller mappe | Hvad bruger du den til? |
|---|---|
| `OPGAVE.md` | Casearbejdets rækkefølge, krav, spørgsmål og checkpoints |
| `DATAORDLISTE.md` | Opslag i centrale data- og domænebegreber |
| `data/raw/` | Uændrede snapshots fra Energinet |
| `data/snapshot_manifest.json` | Filstørrelser, rækkeantal og checksums |
| `src/contracts.py` | Kolonner og navne, som din løsning skal kende |
| `src/pipeline.py` | Dit kode-skelet med nummererede TODO'er |
| `run_pipeline.py` | Kører din pipeline for en valgt periode |
| `output/` | Her skriver du dine egne mellem- og slutfiler |

## Vigtige spilleregler

- Redigér ikke filer i `data/raw/`.
- Bevar rådata og afledte data i forskellige mapper.
- En række må ikke forsvinde lydløst. Flag eller dokumentér fravalg.
- Brug UTC som del af den tekniske join key, og bevar dansk tid til fortolkning.
- Beskriv afregningsdata som senere og mere modnede data—ikke automatisk som den eneste sandhed.
- Brug ikke underviserens referenceimplementation som startkode.

## Hjælp til fejlsøgning

- Hvis `check_setup.py` fejler på en checksum, skal du hente en ny kopi af starterprojektets data hos underviseren.
- Hvis Python ikke kan finde `pandas`, skal du installere `requirements.txt` eller vælge skolens Python-miljø.
- Hvis pipelinen stopper ved en ikke-implementeret TODO, så kontrollér hvilket modul du er i, og følg det aktuelle modul i `OPGAVE.md`.
