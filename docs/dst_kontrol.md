# Modul02 checkpoint

## 1. Realtime-tabel: én række pr. UTC-time og prisområde

| Periode | Rækker | Forventet | Dubletter |
|---|---|---|---|
| dst | 142 | 71 timer × 2 områder | 0 |
| januar | 1.488 | 744 timer × 2 områder | 0 |

`prepare_realtime()` grupperer på `(hour_utc, PriceArea)`, så grain skifter fra
5 min × prisområde til 1 UTC-time × prisområde.

## 2. Kontrol: ingen kunstig ekstra time ved sommertidsskiftet

Aggregeringen sker på `hour_utc` (UTC), ikke dansk lokaltid, som ikke
påvirkes af det lokale spring til sommertid.

- Dst-perioden (28.-30. marts) har 24 + 23 + 24 = **71** lokale timer
  (23 timer den 29. marts, hvor Danmark skifter til sommertid).
- Output har **71 unikke `hour_utc`**, ikke 72.
- Konklusion: ingen kunstig ekstra time opstår ved aggregeringen.

## 3. Ufuldstændige timer (rt_interval_count ≠ 12)

**Dst:** ingen. Alle 142 rækker har præcis 12 intervaller.

*Bemærkning:* metadata advarer om fejlagtige *værdier* omkring
sommertidsskiftet og i `ProductionLt100MW`, men det er ikke det samme som
manglende intervaller. Kompletthed og korrekthed er to forskellige ting.

**Januar:** én ufuldstændig time fundet, i begge prisområder:

| hour_utc | price_area | rt_interval_count |
|---|---|---|
| 2026-01-06 22:00 UTC | DK1 | 9 |
| 2026-01-06 22:00 UTC | DK2 | 9 |

Manglende intervaller: (12−9) × 2 områder = 6, hvilket matcher differencen
i `snapshot_manifest.json` (17.856 forventede mod 17.850 faktiske rækker).
At begge områder mangler samme antal på samme tidspunkt tyder på en fælles
driftshændelse. Rækken er bevaret, ikke slettet; `rt_interval_count = 9` er
selve kvalitetsflaget.

