from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from contracts import (
    EXPECTED_INTERVALS_PER_HOUR,
    EXPECTED_PRICE_AREAS,
    MINIMUM_ANALYSIS_COLUMNS,
    PERIODS,
    REALTIME_REQUIRED_COLUMNS,
    SETTLEMENT_REQUIRED_COLUMNS,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"

PRODUCTION_COLUMNS = [
    "ProductionLt100MW",
    "ProductionGe100MW",
    "OffshoreWindPower",
    "OnshoreWindPower",
    "SolarPower",
]

FOREIGN_EXCHANGE_COLUMNS = [
    "ExchangeGermany",
    "ExchangeNetherlands",
    "ExchangeGreatBritain",
    "ExchangeNorway",
    "ExchangeSweden",
]


class NextTodo(NotImplementedError):
    """Bruges til at pege på næste nummererede trin i starterprojektet."""


def load_records(path: Path, expected_dataset: str) -> pd.DataFrame:
    """Indlæser records og udfører de første kontroller af JSON-konvolutten."""
    if not path.exists():
        raise FileNotFoundError(f"Råfilen findes ikke: {path}")
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("dataset") != expected_dataset:
        raise ValueError(
            f"{path.name} angiver {payload.get('dataset')!r}; "
            f"forventede {expected_dataset!r}."
        )
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError(f"{path.name} mangler en liste med records.")
    if payload.get("total") is not None and int(payload["total"]) != len(records):
        raise ValueError(f"{path.name}: total matcher ikke antallet af records.")
    return pd.DataFrame(records)


def validate_snapshot(
    frame: pd.DataFrame,
    required_columns: list[str],
    timestamp_column: str,
    label: str,
) -> pd.DataFrame:
    """TODO 1: Implementér den fatale datakontrakt.
      Minimum:
    - kontrollér obligatoriske kolonner;
    - konvertér timestampkolonnen og fejl tydeligt på ugyldige værdier;
    - kontrollér DK1/DK2;
    - kontrollér dubletter på timestamp + PriceArea;
    - returnér en kopi med den konverterede timestampkolonne.
    """
    result = frame.copy()

    # Obligatoriske kolonner
    required = set(required_columns) | {timestamp_column, "PriceArea"}
    missing = sorted(required - set(result.columns))
    if missing:
        raise ValueError(f"{label}: obligatoriske kolonner mangler: {missing}")

    # Tidskolonnen: konvertér til UTC-datetime
    parsed = pd.to_datetime(
        result[timestamp_column], utc=True, errors="coerce", format="ISO8601"
    )
    invalid = parsed.isna()
    if invalid.any():
        examples = result.loc[invalid, timestamp_column].head(3).tolist()
        raise ValueError(
            f"{label}: {int(invalid.sum())} ugyldige værdier i "
            f"{timestamp_column}, fx {examples}"
        )
    result[timestamp_column] = parsed


    # Prisområder: kun DK1/DK2
    found = set(result["PriceArea"].dropna().unique())
    unexpected = sorted(found - set(EXPECTED_PRICE_AREAS))
    if unexpected or result["PriceArea"].isna().any():
        raise ValueError(
            f"{label}: uventede prisområder {unexpected} "
            f"eller tomme værdier i PriceArea."
        )

    # Dubletter på nøglen
    duplicated = result.duplicated([timestamp_column, "PriceArea"], keep=False)
    if duplicated.any():
        examples = (
            result.loc[duplicated, [timestamp_column, "PriceArea"]]
            .head(3)
            .astype(str)
            .values.tolist()
        )
        raise ValueError(
            f"{label}: {int(duplicated.sum())} rækker deler nøgle "
            f"({timestamp_column}, PriceArea), fx {examples}"
        )
    return result


def mw_to_mwh(values: pd.Series, interval_minutes: int = 5) -> pd.Series:
    """TODO 2: Beregn MWh som MW × interval_minutes/60.

    Caseantagelse: MW repræsenterer det efterfølgende interval; se DATAORDLISTE.md.
    Resultatet er et tilnærmet sammenligningsgrundlag, ikke officiel afregning.
    """ 
    return values * (interval_minutes / 60)

def prepare_realtime(frame: pd.DataFrame) -> pd.DataFrame:
    """TODO 3: Skab én realtime-række pr. UTC-time og prisområde.

    Outputtet skal mindst indeholde:
    - hour_utc, price_area og rt_interval_count;
    - offshore, onshore og sol i MWh;
    - udenlandsk udveksling uden Storebælt;
    - en prisområdebalance, hvor Storebælt er med;
    - antal negative produktionsintervaller.

    Husk at omregne hvert interval før summering.
    """
    working = frame.copy()

    working["hour_utc"] = working["Minutes5UTC"].dt.floor("h")

    # Omregn HVERT interval til MWh, FØR der summeres.
    mwh_columns = PRODUCTION_COLUMNS + FOREIGN_EXCHANGE_COLUMNS + ["ExchangeGreatBelt"]
    for column in mwh_columns:
        working[column] = mw_to_mwh(working[column])

    # Flag pr. interval: er mindst én produktionskolonne negativ?
    working["is_negative_production"] = (working[PRODUCTION_COLUMNS] < 0).any(axis=1)

    grouped = working.groupby(["hour_utc", "PriceArea"], as_index=False).agg(
        rt_interval_count=("Minutes5UTC", "size"),
        rt_offshore_wind_mwh=("OffshoreWindPower", "sum"),
        rt_onshore_wind_mwh=("OnshoreWindPower", "sum"),
        rt_solar_mwh=("SolarPower", "sum"),
        rt_production_lt100mw_mwh=("ProductionLt100MW", "sum"),
        rt_production_ge100mw_mwh=("ProductionGe100MW", "sum"),
        rt_great_belt_mwh=("ExchangeGreatBelt", "sum"),
        rt_exchange_germany_mwh=("ExchangeGermany", "sum"),
        rt_exchange_netherlands_mwh=("ExchangeNetherlands", "sum"),
        rt_exchange_great_britain_mwh=("ExchangeGreatBritain", "sum"),
        rt_exchange_norway_mwh=("ExchangeNorway", "sum"),
        rt_exchange_sweden_mwh=("ExchangeSweden", "sum"),
        rt_negative_interval_count=("is_negative_production", "sum"),
    )

    # Udenlandsk udveksling UDEN Storebælt.
    grouped["rt_foreign_exchange_mwh"] = grouped[
        [
            "rt_exchange_germany_mwh",
            "rt_exchange_netherlands_mwh",
            "rt_exchange_great_britain_mwh",
            "rt_exchange_norway_mwh",
            "rt_exchange_sweden_mwh",
        ]
    ].sum(axis=1)

    # Prisområdebalance MED Storebælt. Realtime har ingen forbrugskolonne,
    # så dette er en forsyningsbalance (produktion + import), ikke en fuld
    # load-balance som i afregning. Dokumentér denne antagelse i kildeskemaet.
    grouped["rt_area_balance_mwh"] = (
        grouped["rt_production_lt100mw_mwh"]
        + grouped["rt_production_ge100mw_mwh"]
        + grouped["rt_offshore_wind_mwh"]
        + grouped["rt_onshore_wind_mwh"]
        + grouped["rt_solar_mwh"]
        + grouped["rt_foreign_exchange_mwh"]
        + grouped["rt_great_belt_mwh"]
    )

    grouped = grouped.rename(columns={"PriceArea": "price_area"})
    return grouped

def prepare_settlement(frame: pd.DataFrame) -> pd.DataFrame:
    """TODO 4: Skab sammenligningsfelter i afregningsdata.

    Outputtet skal mindst indeholde:
    - hour_utc, hour_dk og price_area;
    - samlet offshore og onshore;
    - sol både uden og med self-consumption;
    - udenlandsk udveksling uden Storebælt;
    - gross consumption.
    """
    raise NextTodo("TODO 4 er ikke implementeret: prepare_settlement() Følg det aktuelle modul i OPGAVE.md.")


def join_and_flag(realtime: pd.DataFrame, settlement: pd.DataFrame) -> pd.DataFrame:
    """TODO 5: Udfør outer join og tilføj kvalitetsflag.

    Brug hour_utc + price_area som join key, og validér én-til-én-kardinalitet.
    Bevar mindst flag for joinstatus og præcis 12 realtime-intervaller.
    Tilføj gerne negative værdier, frosne tilstande og metadataadvarsler.
    """
    raise NextTodo("TODO 5 er ikke implementeret: join_and_flag() Følg det aktuelle modul i OPGAVE.md.")


def create_quality_summary(analysis_ready: pd.DataFrame) -> dict:
    """TODO 6: Lav en lille maskinlæsbar rapport med tællinger.

    Medtag mindst samlet rækkeantal, joinstatus, fulde/ufuldstændige timer
    og antal rækker med hvert kvalitetsflag.
    """
    raise NextTodo("TODO 6 er ikke implementeret: create_quality_summary() Følg det aktuelle modul i OPGAVE.md.")


def write_outputs(
    period: str,
    analysis_ready: pd.DataFrame,
    quality_summary: dict,
) -> tuple[Path, Path]:
    missing = sorted(set(MINIMUM_ANALYSIS_COLUMNS) - set(analysis_ready.columns))
    if missing:
        raise ValueError(f"Analyseoutputtet mangler obligatoriske kolonner: {missing}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / f"analysis_ready_{period}.csv"
    quality_path = OUTPUT_DIR / f"quality_{period}.json"
    analysis_ready.to_csv(csv_path, index=False)
    with quality_path.open("w", encoding="utf-8") as handle:
        json.dump(quality_summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return csv_path, quality_path


def build_realtime_period(period: str) -> tuple[pd.DataFrame, Path]:
    """Kør kun det færdige Modul02-spor og gem mellemoutput."""
    if period not in PERIODS:
        raise ValueError(f"Ukendt periode: {period}")
    realtime_name, _ = PERIODS[period]
    realtime_raw = load_records(
        RAW_DIR / realtime_name, "ElectricityProdex5MinRealtime"
    )
    realtime_valid = validate_snapshot(
        realtime_raw,
        REALTIME_REQUIRED_COLUMNS,
        "Minutes5UTC",
        "realtime",
    )
    realtime_hourly = prepare_realtime(realtime_valid)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"realtime_hourly_{period}.csv"
    realtime_hourly.to_csv(path, index=False)
    return realtime_hourly, path


def run_period(period: str) -> tuple[Path, Path]:
    realtime_hourly, _ = build_realtime_period(period)
    _, settlement_name = PERIODS[period]
    settlement_raw = load_records(
        RAW_DIR / settlement_name, "ProductionConsumptionSettlement"
    )
    settlement_valid = validate_snapshot(
        settlement_raw,
        SETTLEMENT_REQUIRED_COLUMNS,
        "HourUTC",
        "afregning",
    )
    settlement_hourly = prepare_settlement(settlement_valid)
    analysis_ready = join_and_flag(realtime_hourly, settlement_hourly)
    quality_summary = create_quality_summary(analysis_ready)
    return write_outputs(period, analysis_ready, quality_summary)