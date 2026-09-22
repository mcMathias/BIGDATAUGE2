# Dataordliste til Energinet-casen

> **Revision:** 1.2 · 21. september 2026  
> **Status:** ARBEJDSDOKUMENT  
> **Rolle:** Opslagsværk til casebegreber og domænetermer

Brug filen som opslag, når `OPGAVE.md`, metadata eller koden henviser til et begreb. Du behøver ikke læse den fra start til slut før Modul01.

## Grain

Grain beskriver, hvad én række repræsenterer.

- Realtime: én værdi ved et femminutterstidspunkt i ét prisområde; i casens integration repræsenterer den det efterfølgende femminuttersinterval.
- Afregning: én time i ét prisområde.
- Dit endelige output: én UTC-time i ét prisområde.

I denne case skal realtime først aggregeres til én UTC-time pr. prisområde, så de to tidsserier kan sammenlignes på samme grain med et one-to-one join. Det er ikke en generel regel for alle joins: målinger pr. tidspunkt og enhed kan fx beriges med et enhedsregister via et many-to-one join. Grain beskriver rækkens betydning; kardinalitet beskriver, hvor mange rækker der må matche.

## Prisområde

Danmark er opdelt i `DK1` og `DK2`. En måling for DK1 må ikke uden videre sammenlignes med eller lægges oven i DK2. Prisområdet er en del af den sammensatte primærnøgle i begge kildedatasæt.

## Operationelle data

Data, der er tilgængelige hurtigt og bruges tæt på den løbende drift. De kan være foreløbige, estimerede, ufuldstændige eller ukorrigerede.

## Afregningsdata

Senere data, som er behandlet og modnet til afregning og statistik. De kan blive revideret over tid. Et enslydende kolonnenavn er ikke i sig selv bevis på samme forretningsdefinition.

## MW og MWh

- MW er effekt: hvor hurtigt energi produceres eller udveksles.
- MWh er energi over tid.

**Caseantagelse:** Vi behandler værdien ved `Minutes5UTC = t` som repræsentativ effekt for `[t, t + 5 minutter)` og beregner `MW × 5/60`. Det er en approksimation til et sammenligningsgrundlag i MWh, ikke en officiel afregningsværdi. Metadata dokumenterer opskalerede SCADA-effektmålinger, femminuttersopløsning og gyldighedstidspunkt; de fastslår ikke entydigt middelværdi over netop det efterfølgende interval.

Casens beregningsregel er:

```text
MWh = MW × 5/60
```

Omregn hvert interval og summér derefter til timer.

Kilde: [Energinets datasætmetadata](https://api.energidataservice.dk/meta/dataset/ElectricityProdex5MinRealtime), description/comment og Minutes5UTC, kontrolleret 21. september 2026. Energinets [datakatalog](https://www.energidataservice.dk/Datakatalog_DA.pdf), s. 8–9 og 37, omtaler interpoleret gennemsnitseffekt og tilnærmet energi, men afgør ikke den præcise femminuttersplacering.

## UTC og dansk tid

UTC er stabil som teknisk tidsnøgle. Dansk tid er nødvendig, når mennesker skal fortolke datoer og klokkeslæt. Ved skiftet til sommertid kan et lokalt døgn have 23 timer.

## Primærnøgle og join key

Energinets metadata markerer en sammensat **primærnøgle (primary key)** i hvert kildedatasæt:

- realtime: `(Minutes5UTC, PriceArea)`;
- afregning: `(HourUTC, PriceArea)`.

Efter timeaggregation identificeres én realtime-række ved `(hour_utc, price_area)`. Når realtime- og afregningsdata sammenkobles, bruges de samme to felter som **join key**. En join key beskriver de felter, der bruges til sammenkoblingen; den er ikke det samme begreb som en key/property i et JSON-object.

Det endelige analyseoutput skal fortsat have én række pr. `(hour_utc, price_area)`.

## Storebælt

Storebæltsforbindelsen flytter energi mellem DK1 og DK2. Den er derfor:

- ikke udenlandsk udveksling for Danmark;
- relevant for balancen i hvert af de to prisområder.

## Strukturel null-værdi

En tom værdi kan betyde, at en forbindelse ikke findes i det pågældende prisområde. Det er noget andet end en ukendt måling. Du skal undersøge kolonnen og dokumentere, hvorfor en null eventuelt behandles som nul.

## Kvalitetsflag

En kolonne, der fortæller, om en række kræver særlig opmærksomhed. Flag gør det muligt at bevare data og samtidig være tydelig om problemer.

Eksempler:

- ufuldstændig realtime-time;
- række findes kun i én kilde;
- negativ produktionsværdi;
- mistænkeligt uændrede værdier;
- kendt fejl omtalt i metadata.

## WAPE

Weighted Absolute Percentage Error sammenfatter den samlede absolutte afvigelse i forhold til den samlede størrelse af referenceværdierne:

```text
WAPE = sum(abs(realtime - afregning)) / sum(abs(afregning)) × 100
```

WAPE er valgfri i minimumsløsningen. Et fejlmål erstatter ikke undersøgelse af enkelte timer, definitioner og datakvalitet.

## Revisionshistorik

| Revision | Dato | Ændring |
|---|---|---|
| 1.2 | 21. september 2026 | Præciserer arbejdsrute og forklaringer uden nye casekrav. |
| 1.0 | 21. september 2026 | QA-001. |
| 1.1 | 21. september 2026 | Gør filens opslagsrolle tydelig og skelner mellem primærnøgle, join key og JSON object key. |
