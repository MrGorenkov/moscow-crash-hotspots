# Data notes: «Карта ДТП» (dtp-stat.ru) open data for Moscow

Checked on 2026-09-23. All counts below come from a direct parse of the downloaded file (Python `json`, grouped by `datetime[:4]`). No modelling was done.

## 1. Files in this folder

| File | Size (bytes) | Notes |
|---|---|---|
| `moskva.geojson.zip` | 14,365,498 | Downloaded from https://dtp-stat.ru/media/opendata/moskva.geojson.zip. HTTP `Last-Modified: Thu, 26 Feb 2026 12:27:49 GMT`. SHA-256 `430FB00B76BFC0BEA4240C4DDB1C4CBC1F1089884591FA3AFE2135BF093BBAEF` |
| `moskva.geojson` | 206,584,196 | Unzipped. GeoJSON `FeatureCollection`, **94,786 features**, `Point` geometry as `[lon, lat]` (WGS-84 degrees) |

The download page (https://dtp-stat.ru/opendata/) lists the file as «Москва — январь 2015 - январь 2026 — 13.60 mb — Скачать .geojson».

## 2. Two data products on dtp-stat.ru (important for the severity model)

1. **Regional GeoJSON** (the file above): one file per region with a simplified schema, described below.
2. **Russia-wide yearly JSON** with the full ГИБДД card schema: `https://dtp-stat.ru/media/years/{YYYY}.json.7z` for 2015–2026. Each file is 9.5–13 MB compressed and 441–639 MB unpacked. A combined `2015-2026.json.7z` is 118 MB compressed and **5.9 GB unpacked**. Not downloaded into this folder because of the unpacked size; see §6.
   - I checked `2025.json.7z` in a scratch folder (10,128,220 bytes, `Last-Modified: 05 Mar 2026`). It contains 130,444 Russian records. **8,354** of them have `"г. Москва"` in `REGIONS`, which is exactly the 2025 count in the GeoJSON. **All 8,354 IDs match** (`EM_NUMBER` = GeoJSON `gibdd_number`), so the two products can be joined 1:1.

## 3. Records per year (Moscow GeoJSON)

| Year | Crashes (records) | Killed (Σ dead_count) | Injured (Σ injured_count) |
|---|---|---|---|
| 2015 | 10,299 | 662 | 11,797 |
| 2016 | 8,308 | 525 | 9,427 |
| 2017 | 8,256 | 462 | 9,424 |
| 2018 | 9,073 | 460 | 10,372 |
| 2019 | 9,211 | 440 | 10,628 |
| 2020 | 7,913 | 373 | 8,911 |
| 2021 | 8,438 | 356 | 9,555 |
| 2022 | 7,641 | 299 | 8,735 |
| 2023 | 8,042 | 305 | 8,914 |
| 2024 | 8,859 | 342 | 9,826 |
| 2025 | 8,354 | 299 | 9,293 |
| 2026 (January only) | 392 | 11 | 461 |
| **Total** | **94,786** | | |

- Date range: `2015-01-01 00:23` to `2026-01-31 23:45`. **Eleven full years (2015–2025)** allow ten train(t)→test(t+1) pairs.
- No duplicate `id` and no duplicate `gibdd_number`.
- **External consistency check (official source):** mos.ru (27.01.2023) reports 300 road deaths in Moscow in 2022 and 58 fewer than in 2021, i.e. ≈358. The dataset gives 299 (2022) and 356 (2021). https://www.mos.ru/mayor/themes/2299/8905050/
- Only crashes with killed or injured people are included (ГИБДД «учётные ДТП»). 3 records are labelled «Без пострадавших (нет данных)».

## 4. Field list (GeoJSON), with example values

**Crash level** (`feature.properties`)

| Field | Meaning | Example / distribution (all years) |
|---|---|---|
| `id` | dtp-stat id | 6 |
| `gibdd_number` | ГИБДД card number (join key to the yearly JSON `EM_NUMBER`) | "157054063" |
| `datetime` | local date-time | "2015-01-01 00:23:00" |
| `point` {lat,long} / `geometry` | coordinates | 55.689444, 37.608056 |
| `address` | address string | "г Москва, ул Черемушкинская Б., 1" |
| `region` | municipal district or settlement (147 distinct) | «Выхино-Жулебино» (1,467), «Пресненский» (1,401); «Москва» = unassigned (1,429) |
| `parent_region` | «Москва» or null | null for 1,429 records |
| `category` | crash type (19 values) | Столкновение 42,461; Наезд на пешехода 32,792; Наезд на препятствие 5,019; Падение пассажира 4,412; Наезд на стоящее ТС 4,095; Наезд на велосипедиста 3,884; Опрокидывание 1,615; Наезд на лицо, использующее СИМ 63 |
| `severity` | dtp-stat derived severity | Тяжёлый 53,905; Легкий 36,670; С погибшими 4,208; Без пострадавших 3. **⚠ Not comparable across years, see §5.1** |
| `light` | lighting | Светлое время суток 57,321; Темное, освещение включено 35,369; Сумерки 1,434; Темное, освещение отсутствует 484; …не включено 177 |
| `weather` (list) | weather | Пасмурно 47,120; Ясно 42,172; Дождь 4,098; Снегопад 1,948; Туман 35 |
| `road_conditions` (list) | **road deficiencies (НДУ), not surface state** | Не установлены 82,541; no/poor horizontal markings 4,669; missing signs 4,482; wrong/poorly visible signs 3,082; … |
| `nearby` (list) | road-network objects at or near the site | Перегон 49,362; Регулируемый перекресток 13,227; Нерегулируемый пешеходный переход 12,539; Остановка ОТ 11,373 |
| `scheme` | ГИБДД crash scheme code | "610" |
| `participant_categories` (list) | flags | Пешеходы 34,122; Дети 9,567; Мотоциклисты 8,441; Велосипедисты 4,618; Общ. транспорт 1,483 |
| `dead_count`, `injured_count`, `participants_count` | counts | 1, 1, 2 |
| `tags` | always «Дорожно-транспортные происшествия» | |

**Vehicle level** (`vehicles[]`, 162,648 vehicles): `year` (production year), `brand`, `model`, `color`, `category` (B-класс 41,207; C-класс 28,892; Мотоциклы 7,272; Велосипеды 3,676; …).

**Participant level** (`vehicles[].participants[]` and `participants[]` for pedestrians etc.; 231,375 persons): `id`, `role` (Водитель 154,488; Пешеход 34,456; Пассажир 33,422; Велосипедист 3,332; …), `gender`, `violations` (list; top: Неправильный выбор дистанции 16,441; Нарушение правил проезда пешеходного перехода 11,232; Несоблюдение очередности проезда 11,046; Несоответствие скорости 9,225), `health_status` (full ГИБДД wording), `years_of_driving_experience`.

**Available only in the yearly JSON** (verified on Moscow 2025): `TRAFFIC_AREA_STATE` (Сухое 5,921; Мокрое 2,057; Обработанное ПГМ 247; Заснеженное 107; Гололедица 11), `STREET_SIGN` (street category, e.g. Магистральные улицы общегородского значения 1,411), `ROAD_SIGN`, `ROAD_TYPE`, `MT_RATE`, `MOTION_INFLUENCES` (e.g. «Сужение проезжей части припаркованным транспортом» 764), `DEFECTS`, split `RD_CONSTR_HERES/THERES`, `VEH_AMOUNT`, `CHILDREN_ATTR`. Per vehicle: `OKFS/OKOPF` (ownership), `RUDDER_TYPE`, `TECH_FAILURE_TYPE`, `ESCAPE`. Per person: `SAFETY_BELT` (Да 12,929 / Нет 3,560 among vehicle occupants in 2025), `MED_RESULT_PERMILLE` (188 persons > 0 in 2025), `CHILD_SAFETY_TYPE`, `MAIN_PDD_DERANGEMENT` vs `ATTENDANT_PDD_DERANGEMENT`, `INJURED_CARD`.
→ For the severity model, **join the yearly JSON on `gibdd_number`**. Surface state, street category, seat belt and alcohol are standard severity predictors and are missing from the GeoJSON.

## 5. Data-quality caveats

### 5.1 Break in severity coding in 2020 (critical for the severity model)
- Severity by year (dtp-stat `severity`):

  | Year | Легкий | Тяжёлый | С погибшими |
  |---|---|---|---|
  | 2019 | 6,684 | 2,120 | 407 |
  | 2020 | **0** | **7,574** | 339 |
  | 2021 | 1,372 | 6,736 | 330 |
  | 2025 | 1,202 | 6,865 | 285 |

- Cause, found in the code and data: the dtp-stat backend (`data/utils.py`, repo dtpstat/dtp-stat) assigns severity by keyword. «Легкий» ← ['разовой', 'амбулатор']; «Тяжёлый» ← ['стационар']; «С погибшими» ← ['скончался']. From 2020 the ГИБДД health status «Раненый, находящийся (находившийся) на амбулаторном лечении, **либо в условиях дневного стационара**» replaces the old outpatient wording. It contains «стационар», so it is mapped to «Тяжёлый» (32,773 crashes). In the data, «Тяжёлый» = 21,127 crashes whose worst injury is inpatient (стационар) + 32,773 whose worst injury is outpatient/day-stationary (new wording).
- Context: the new ДТП accounting rules (Постановление Правительства РФ от 19.09.2020 № 1502, in force 01.01.2021) define «раненый» as a person treated «в стационарных условиях на срок не менее одних суток либо в амбулаторных условиях или в условиях дневного стационара» (text checked at base.garant.ru/74680240/). That this wording change drives the 2020 break is my inference.
- **Recommendation:** do **not** use `severity` as the target. Rebuild a consistent crash-level target from participant `health_status`, e.g. **KSI = ≥1 killed or ≥1 inpatient («стационарном лечении»)**. Its share is 0.356 (2015), 0.273 (2019), 0.242 (2020), 0.201 (2022), 0.182 (2025). It still drifts down, so add year as a feature or check stability of the drift, and report sensitivity to the 2020–2021 break. Alternative binary target: fatal vs non-fatal (30-day death definition).
- The health-status category «Получил телесные повреждения с показанием к лечению…» appears only from 2021 (1,469–1,675 persons/yr). «Не определен»: 300–500 persons/yr.

### 5.2 Coordinates
- 94,003 of 94,786 (99.17 %) fall inside a Moscow bounding box (55.0–56.1 N, 36.7–38.0 E).
- Problems: 37 null geometries; 419 placeholder points at exactly (55, 37); 49 at ≈(0, 0); 42 with swapped lat/lon; 236 other out-of-box points (e.g. 52.37 N). **All 783 problematic records are from 2015–2018** (2015: 410; 2016: 182; 2017: 154; 2018: 37). There are none from 2019 on.
- 93 exact coordinate pairs are shared by ≥10 crashes (1,856 crashes). These are likely geocoded to a road-km marker or address centroid, which inflates point density. Consider de-duplication or jitter sensitivity for KDE and DBSCAN.
- The project says coordinates were corrected: «эти данные приведены с изменениями (например, корректировки координат)». The backend keeps manually verified points (`point_is_verified`). Otherwise it takes ГИБДД `COORD_L/COORD_W`.
- Moscow's territory includes New Moscow; decide whether to restrict to inside MKAD or to old Moscow, or use the full city with an exposure layer.

### 5.3 Other caveats
- No exposure data (traffic volume, VKT), so hotspots are density-based, not risk-based. Consider OSM road length per cell as a denominator for PAI/NKDE.
- The project wiki (github.com/dtpstat/dtp-project/wiki, page `stat.gibdd.ru`) records an outage of the ГИБДД portal from June 2021 to about October 2021. 2021 counts look complete (8,438).
- The file is a living dataset: ГИБДД cards can be edited later. Freeze the file you analyse, citing the SHA-256 above, and give the download date in the paper.
- 2020 has lower counts (7,913), plausibly from COVID-19 mobility restrictions (my inference). Treat 2020→2021 train/test pairs with care.
- `region` has 1,429 records with the generic «Москва» and null `parent_region`.

## 6. License and terms of use

- dtp-stat.ru, site footer (every page): **«Использование материалов возможно с указанием активной ссылки на сайт»**.
- Open-data page: «Здесь вы можете скачать данные по ДТП, чтобы **использовать их в исследованиях** и анализировать с помощью своих инструментов. Первоисточник данных – официальный сайт ГИБДД, но эти данные приведены с изменениями (например, корректировки координат).»
- GitHub (org `dtpstat`): backend `dtp-stat` GPL-3.0, `website` GPL-3.0, `dtpstat-map-server` GPL-3.0, `dtp-stat-archive` GPL-2.0. These licenses cover the **code**, not the data. No separate data license (e.g. CC) is stated.
- **Conclusion:** use in a publication is permitted, with required attribution: a link to dtp-stat.ru plus the original source, ГИБДД. Redistributing the raw file is not explicitly addressed. Share code and derived aggregates and link to the original download.
- Suggested footnotes, in journal style:
  - Карта ДТП: открытые данные [сайт]. Карта ДТП; 2026 [обновлено 26 февраля 2026; процитировано …]. Доступно: https://dtp-stat.ru/opendata/
  - Показатели состояния безопасности дорожного движения [сайт]. Госавтоинспекция МВД России; [процитировано …]. Доступно: http://stat.gibdd.ru/
- Project team (dtp-stat.ru/pages/about/): Алексей Радченко, Анастасия Ромашкевич (co-founders), Александр Март, Михаил Шеховцов. Contact: dtp.stat@gmail.com. Optional: notify the team or ask about a preferred citation.

## 7. Original source

- ГИБДД portal «Показатели состояния безопасности дорожного движения», http://stat.gibdd.ru/. Crash cards from 2015 onward. dtp-stat parses them (backend README: «Backend + Parser stat.gibdd.ru»).
- Recording rules: until 31.12.2020 the 1995 rules applied; from 01.01.2021, Правила учета ДТП per ПП РФ № 1502 (19.09.2020). «Погибший» means death within 30 days.
