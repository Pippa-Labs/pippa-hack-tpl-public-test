# App ideas you can finish today

You have about two hours. The goal is one working app that Pippa really
reaches for, not four half-built ones.

Pick an idea, paste it into Claude Code along with your repository link, and
let Claude build it. You do not write the code, install anything or run
anything.

Everything here respects the rules in `CLAUDE.md`:

- No user accounts, no log-ins, no OAuth. Your app is never given anyone's
  credentials, and publishing refuses a manifest that asks for them.
- No database and no memory. A fresh copy of your app is built for every call
  and thrown away. Nothing written to a file or a global survives.
- Twenty seconds, hard. Past that the call is killed.
- Python 3.12 standard library, plus `pippa_agentapp_sdk` and `PyYAML`.
  Nothing else is installed where your app runs. HTTP means `urllib.request`,
  not the `requests` library.
- The whole package must stay under 3 MB.

---

## Read this before you pick: what gets used

**Build something that answers with a fact or a figure.**

We measured this against the live system. Apps that return a number, a time, a
name or a yes-or-no get used. Apps that mainly rewrite or generate text
usually do not, because Pippa answers those herself before an app is ever
consulted.

| Gets used | Usually does not |
|---|---|
| calculations and conversions | translating |
| live lookups — weather, tides, transport, prices, air quality | summarising, rewriting |
| anything about a named place | writing poems, names, copy |
| anything about a date or a time | definitions, acronyms |
| anything worked out from numbers the user gives | explaining how something works |
| | choosing for the user, opinions |

An app in the right-hand column is not broken. It never gets asked. From the
outside the two look identical, which is why this is worth a minute now rather
than an hour later.

Every idea below is in the left-hand column. If you have an idea of your own,
check which column it sits in first. If it is borderline, sharpen it until it
is a lookup or a calculation: "write me a packing list" is in the right-hand
column, "what will the temperature be in Oslo on Friday" is in the left.

---

## What makes a good agent app idea

An Agent App is not a website and not a chatbot. Pippa hands it a few values
pulled out of what the user said, the app returns structured facts, and Pippa
writes the sentence around them. So a good idea has five properties.

**1. A person would actually say it out loud.**
"How long until my train" is app-shaped. "Query the departure board" is not. If
you cannot imagine someone typing it to an assistant without thinking about it,
the app will never be chosen.

**2. The answer is facts, not prose.**
Numbers, names, dates, yes-or-no. Those become fields in your manifest's
`output`. If the honest answer to your idea is "a paragraph", the idea belongs
to Pippa, not to an app.

**3. Pippa could not answer it from memory.**
This is the table above, said another way. Pippa already knows who wrote
*Hamlet*. Three kinds of question are safe:

- **Current** — it changes faster than anything a model was trained on. Today's
  weather, the line status, the exchange rate, the air quality.
- **Personal context** — the answer depends on something the user says in the
  message. Their postcode, their loan amount, their two dates, their pace.
- **Computational** — it needs exact arithmetic. Models are unreliable at
  arithmetic and completely reliable at describing arithmetic someone else did.

**4. It is one job.**
One outcome done well beats four vague ones. Two outcomes is the sensible
maximum for a hackathon, and only if they use clearly different words.

**5. You can say five different ways a person would ask for it.**
Those become `example_phrases`, which is how Pippa decides to use your app at
all. If you cannot think of five, the idea is not app-shaped yet. Change the
idea, not the phrases.

### Shaping the output

The manifest's type vocabulary is deliberately small: `string`, `integer`,
`number`, `boolean`, `datetime`, `duration`, `timezone`, `array`, `object`.

Two things to know before Claude designs your `output`:

- An `array` must declare an `item_type`, and it only goes one level deep.
- An `object` has no inner shape you can declare, so nobody downstream knows
  what is inside it.

In practice: prefer a flat set of named fields, plus arrays of plain strings
for lists. "Three facts and a list of short strings" is a better output than
one nested blob.

### Budgeting your twenty seconds

- Every request needs a timeout: `urllib.request.urlopen(req, timeout=5)`.
  Without one, a slow server can hang far past the limit.
- One or two HTTP requests is comfortable. Thirty is not.
- If an idea needs a list of 500 items fetched one at a time, take a slice of
  ten and say so in the `narrative`.
- Some public APIs ask for a descriptive `User-Agent` header and return 403
  without one. Nominatim and the Wikimedia APIs both do.

Claude writes the tests for all of this in `test_app.py`, and the build runs
them on every push. A test that fails stops the deploy, so nothing broken
reaches Pippa.

---

## Tier 1 — no network at all

These cannot fail because somebody else's server is slow. If you are unsure
whether you will finish, start here.

### 1. Split the bill

Work out who owes what on a shared bill, including tip and uneven shares.

- **Outcome** `bill.split`
- **Inputs** `total` (number), `people` (integer), `tip_percent` (number,
  optional), `extra_shares` (integer, optional, for the person who had the
  lobster)
- **Outputs** `per_person` (number), `total_with_tip` (number), `tip_amount`
  (number), `remainder_pence` (integer)
- **Public API** None.
- **Hardest part** Deciding who absorbs the leftover penny, because the parts
  have to add back up to the total or the app is wrong in a way people notice.

### 2. Kitchen and oven converter

Convert cooking measurements, including gas mark, fan and conventional ovens.

- **Outcomes** `units.convert` and `oven.convert`
- **Inputs** For `units.convert`: `quantity` (number), `from_unit` (string),
  `to_unit` (string). For `oven.convert`: `temperature` (number), `scale`
  (string).
- **Outputs** `value` (number), `unit` (string), `display` (string), plus
  `gas_mark` (string), `celsius` (integer), `fahrenheit` (integer),
  `fan_celsius` (integer) for the oven outcome.
- **Public API** None.
- **Hardest part** Grams of flour and grams of water are not the same volume,
  so decide early whether to support ingredient densities or to refuse
  mass-to-volume conversions honestly.

### 3. Pace and finish time

Running or cycling pace, split times and a projected finish.

- **Outcome** `pace.calculate`
- **Inputs** `distance` (string, e.g. "10k", "half marathon", "5 miles"),
  `time` (string, optional), `pace` (string, optional)
- **Outputs** `pace_per_km` (string), `pace_per_mile` (string), `finish_time`
  (string), `speed_kmh` (number), `splits` (array of string)
- **Public API** None.
- **Hardest part** People say it three ways — distance plus time, distance plus
  pace, or time plus pace — so the input descriptions must tell the extractor
  to leave the missing one empty instead of inventing it.

### 4. Loan or mortgage repayment

Monthly payment, total interest, and what overpaying really saves.

- **Outcome** `loan.repayment`
- **Inputs** `amount` (number), `annual_rate` (number), `years` (integer),
  `monthly_overpayment` (number, optional)
- **Outputs** `monthly_payment` (number), `total_interest` (number),
  `total_paid` (number), `months_saved` (integer), `interest_saved` (number)
- **Public API** None.
- **Hardest part** The overpayment answer is an amortisation loop rather than a
  formula, and rounding each month to the nearest penny is what makes the total
  match what a bank would say.

### 5. What time will it be there?

Convert a time between places, and say what the local time is in each.

- **Outcome** `timezone.convert`
- **Inputs** `time` (string), `from_zone` (timezone), `to_zones` (array of
  timezone), `date` (string, optional)
- **Outputs** `converted` (array of string), `earliest_local` (string),
  `latest_local` (string), `hours_apart` (number),
  `all_within_working_hours` (boolean)
- **Public API** None. `zoneinfo` is in the standard library and knows every
  IANA zone and every daylight-saving rule.
- **Hardest part** Daylight saving means the answer depends on the date, so
  decide what the app assumes when the user gives only a time, and say so in
  the narrative.

Routing note: avoid phrases containing "my calendar", "my schedule" or "what's
on". Those belong to Pippa Diary and your app will lose to it. Use "what time
would it be in", "how many hours ahead is", "convert to time".

### 6. Percentages, VAT and discounts

The arithmetic people get wrong in a shop or on an invoice.

- **Outcome** `percent.work_out`
- **Inputs** `amount` (number), `percent` (number, optional), `second_amount`
  (number, optional), `form` (string, optional — "percent of", "percent off",
  "add VAT", "remove VAT", "percentage change")
- **Outputs** `result` (number), `difference` (number), `percent_used`
  (number), `form_used` (string)
- **Public API** None. The UK standard VAT rate is 20%, so removing it is
  dividing by 1.2, which is the sum most people get wrong.
- **Hardest part** At least five different questions hide in the word
  "percent", so the input descriptions have to make the extractor say which
  one, and the app has to return `form_used` so the answer is checkable.

---

## Tier 2 — one public API, comfortably finishable

Each of these is one or two HTTP requests. Every API named here is free, needs
no key and needs no sign-up.

### 7. Working days between two dates

Count business days between two dates, skipping weekends and public holidays.

- **Outcome** `workdays.between`
- **Inputs** `start_date` (string), `end_date` (string), `country` (string,
  optional, ISO code such as "GB")
- **Outputs** `working_days` (integer), `total_days` (integer), `weekend_days`
  (integer), `holidays_skipped` (array of string)
- **Public API** Nager.Date, no key:
  `https://date.nager.at/api/v3/PublicHolidays/2026/GB`
- **Hardest part** The holiday list is per year, so a range that crosses New
  Year needs two requests and a merge.

### 8. Do I need a coat?

Weather for a named place, as numbers plus a yes-or-no drawn from them.

- **Outcome** `weather.outlook`
- **Inputs** `place` (string), `when` (string, optional)
- **Outputs** `max_temp_c` (number), `min_temp_c` (number),
  `rain_chance_percent` (integer), `wind_kph` (number), `coat` (boolean),
  `umbrella` (boolean), `place_used` (string)
- **Public API** Open-Meteo, no key:
  `https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=-0.13&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max`
  For the place name, either Open-Meteo's own geocoder
  (`https://geocoding-api.open-meteo.com/v1/search?name=Bristol`) or Nominatim
  (`https://nominatim.openstreetmap.org/search?q=Bristol&format=json`, which
  needs a `User-Agent` header).
- **Hardest part** Turning a place name into coordinates, and deciding what to
  do when the name matches three towns — pick the first and return
  `place_used` so Pippa can say which one was meant.

Routing note: "today" and "tomorrow" belong to Pippa Diary. Build the phrases
around "do I need a coat in", "will it rain in", "what's the weather like in".

### 9. Currency at the published rate

Convert an amount using a real, dated exchange rate.

- **Outcome** `money.convert`
- **Inputs** `amount` (number), `from_currency` (string), `to_currency`
  (string)
- **Outputs** `converted` (number), `rate` (number), `inverse_rate` (number),
  `rate_date` (string)
- **Public API** Frankfurter, no key, European Central Bank reference rates:
  `https://api.frankfurter.app/latest?from=GBP&to=EUR`
- **Hardest part** Currency names are ambiguous — "dollars" is at least five
  currencies — so the input description must tell the extractor to return the
  three-letter code or an empty string, never a guess.

### 10. Air quality right now

How clean the air is at a named place, and what the worst pollutant is.

- **Outcome** `air.quality`
- **Inputs** `place` (string)
- **Outputs** `european_aqi` (integer), `band` (string), `pm2_5` (number),
  `pm10` (number), `worst_pollutant` (string), `place_used` (string),
  `checked_at` (datetime)
- **Public API** Open-Meteo air quality, no key:
  `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=51.5&longitude=-0.13&hourly=pm10,pm2_5,european_aqi`
  Geocode the place with Open-Meteo's geocoder or Nominatim.
- **Hardest part** The response is hourly, so the app has to pick the reading
  nearest `call.context.now` rather than the first one in the list, and turn
  the index into a band a person understands.

### 11. Sunrise, sunset and day length

What time it gets light and dark at a named place, and how much daylight there
is.

- **Outcome** `daylight.times`
- **Inputs** `place` (string), `date` (string, optional)
- **Outputs** `sunrise` (datetime), `sunset` (datetime), `day_length_hours`
  (number), `minutes_change_since_yesterday` (integer), `place_used` (string)
- **Public API** Sunrise Sunset, no key:
  `https://api.sunrise-sunset.org/json?lat=51.5&lng=-0.13&formatted=0`
  Geocode the place first. Open-Meteo's daily forecast also returns `sunrise`,
  `sunset` and `daylight_duration` if you would rather make one request.
- **Hardest part** The times come back in UTC, so they must be converted to the
  place's own time zone before anyone reads them — and `zoneinfo` needs an IANA
  name, which the geocoder gives you.

### 12. Flood warnings near a place

Current flood warnings and alerts for somewhere in England.

- **Outcome** `flood.warnings`
- **Inputs** `place` (string), `radius_km` (integer, optional)
- **Outputs** `warning_count` (integer), `highest_severity` (string), `areas`
  (array of string), `any_severe` (boolean), `checked_at` (datetime)
- **Public API** UK Environment Agency flood-monitoring API, no key:
  `https://environment.data.gov.uk/flood-monitoring/id/floods`
  It accepts `?lat=&long=&dist=` for a radius search. Use postcodes.io
  (`https://api.postcodes.io/postcodes/BS14ST`) or a geocoder for coordinates.
- **Hardest part** "Near" has to mean a radius passed to the API, not a polygon
  worked out by hand, and no warnings is a good answer rather than an error.

### 13. Is my line running?

Status of London Underground, DLR and Elizabeth line services.

- **Outcome** `tube.status`
- **Inputs** `line` (string, optional — empty means all lines)
- **Outputs** `disrupted_count` (integer), `worst_status` (string),
  `disrupted_lines` (array of string), `good_service` (boolean),
  `checked_at` (datetime)
- **Public API** ~~TfL unified API~~ — **does not work from here.** Measured
  2 Nov 2026: `https://api.tfl.gov.uk/Line/Mode/tube/Status` returns
  **`403`, `error code: 1010`** — a Cloudflare block on the caller, with and
  without an `app_key`. Nothing you write fixes that. Pick another idea, or
  find a source that will answer you; the outcome shape below is still a good
  one if you do.
- **Hardest part** The response is deeply nested and an `object` has no inner
  shape you can declare, so flatten each line to a readable string before it
  goes into an array.

### 14. Recent earthquakes

Quakes in the last day or week, optionally above a magnitude.

- **Outcome** `quakes.recent`
- **Inputs** `minimum_magnitude` (number, optional), `period` (string,
  optional, "day" or "week")
- **Outputs** `count` (integer), `largest_magnitude` (number), `largest_place`
  (string), `most_recent_time` (datetime), `events` (array of string)
- **Public API** USGS GeoJSON feeds, no key:
  `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson`
- **Hardest part** The all-quakes feed is large, so pick the pre-filtered feed
  that matches the question and cap how many events come back.

### 15. What is at the top of Hacker News?

The top stories right now, with their scores and how old they are.

- **Outcome** `hn.top`
- **Inputs** `topic` (string, optional), `count` (integer, optional)
- **Outputs** `stories` (array of string), `matched` (integer), `top_score`
  (integer), `median_age_hours` (number), `checked_at` (datetime)
- **Public API** Hacker News Firebase API, no key:
  `https://hacker-news.firebaseio.com/v0/topstories.json` then
  `https://hacker-news.firebaseio.com/v0/item/38123456.json`
- **Hardest part** You get 500 ids and then one request per story, which is the
  easiest way in this whole document to spend twenty seconds — take the first
  thirty ids at most and stop. Return titles and scores as they are published;
  do not try to summarise them, because that is Pippa's job and she is better
  at it.

### 16. Is now a good time to run the washing machine?

How clean the British electricity grid is right now, and when it will be
cleanest.

- **Outcome** `grid.intensity`
- **Inputs** `postcode` (string, optional)
- **Outputs** `intensity_gco2_kwh` (integer), `index` (string),
  `cleanest_hour_start` (datetime), `cleanest_intensity` (integer),
  `top_fuel` (string)
- **Public API** Carbon Intensity API, no key:
  `https://api.carbonintensity.org.uk/intensity`
  `https://api.carbonintensity.org.uk/regional/postcode/BS1`
- **Hardest part** The forecast arrives in half-hour blocks, so "the cleanest
  time" is a scan across blocks rather than a field you read.

### 17. Where is the space station?

The ISS position right now, and how far it is from a place you name.

- **Outcome** `iss.position`
- **Inputs** `place` (string, optional)
- **Outputs** `latitude` (number), `longitude` (number), `altitude_km`
  (number), `over_ocean` (boolean), `distance_km` (integer), `checked_at`
  (datetime)
- **Public API** Where the ISS at, no key:
  `https://api.wheretheiss.at/v1/satellites/25544`
  Geocode the place with Open-Meteo or Nominatim.
- **Hardest part** Resisting the urge to answer "can I see it from here", which
  is a real orbital-visibility calculation — return the great-circle distance
  and be honest that is what was computed.

### 18. Next trains from a German station

Departures in the next hour, with delays.

- **Outcome** `rail.departures`
- **Inputs** `station` (string), `minutes_ahead` (integer, optional)
- **Outputs** `station_name` (string), `departures` (array of string),
  `delayed_count` (integer), `next_departure` (datetime)
- **Public API** The Deutsche Bahn community API, no key:
  `https://v6.db.transport.rest/locations?query=Berlin%20Hbf` then
  `https://v6.db.transport.rest/stops/8011160/departures?duration=60`
- **Hardest part** Resolving a station name to an id is a separate request, so
  that is two round trips before there is any data — set a short timeout on
  both.

### 19. Sea conditions at a named beach

Wave height and sea temperature where somebody is thinking of swimming.

- **Outcome** `sea.conditions`
- **Inputs** `place` (string)
- **Outputs** `wave_height_m` (number), `sea_temp_c` (number), `flat`
  (boolean), `place_used` (string), `checked_at` (datetime)
- **Public API** Open-Meteo Marine, no key:
  `https://marine-api.open-meteo.com/v1/marine?latitude=50.82&longitude=-0.14&hourly=wave_height,sea_surface_temperature`
  Geocode the beach name with Open-Meteo's geocoder or Nominatim first.
- **Hardest part** The marine grid is offshore, so a place a few miles inland
  returns nothing — detect the empty response and raise `AgentAppError` with a
  `user_message` saying the place is not on the coast, rather than returning
  zeroes.

---

## Tier 3 — ambitious

These need two sources, or a judgement call you have to defend. Attempt one of
these only if your first outcome already works.

### 20. What is everyone reading about?

How much attention a topic is getting on Wikipedia, as daily view counts.

- **Outcome** `wiki.attention`
- **Inputs** `topic` (string), `days` (integer, optional)
- **Outputs** `article` (string), `total_views` (integer), `daily_average`
  (integer), `peak_day` (string), `peak_views` (integer), `trend` (string)
- **Public API** Wikimedia REST, no key, but it requires a descriptive
  `User-Agent` header or it returns 403:
  `https://en.wikipedia.org/api/rest_v1/page/summary/Tardigrade` to resolve the
  title, then
  `https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Tardigrade/daily/20261001/20261020`
- **Hardest part** The pageviews endpoint needs the exact article title, so it
  has to be resolved first, and the app must return which article it measured.

### 21. When is the next dry spell?

Scan the hourly forecast for a named place and return the next block of hours
with no rain in it.

- **Outcome** `dry.window`
- **Inputs** `place` (string), `hours_needed` (integer, optional)
- **Outputs** `start` (**string**), `end` (**string**),
  `max_rain_chance_percent` (integer), `max_temp_c` (number), `wind_kph`
  (number), `hours_found` (integer), `place_used` (string),
  `timezone_used` (string), `threshold_percent` (integer)
- **Public API** Open-Meteo hourly, no key:
  `https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=-0.13&hourly=temperature_2m,precipitation_probability,wind_speed_10m&timezone=auto&forecast_days=3`
- **Not `datetime`.** These were `datetime` here and the platform would have
  refused them: a `datetime` output must carry a UTC offset, and Open-Meteo
  with `timezone=auto` returns `2026-11-04T14:00` with none. Return the local
  clock time as a `string` and say which zone in `timezone_used`. The same
  correction applies to the sunrise, air-quality and sea-conditions ideas.
- **Hardest part** Keeping it a measurement rather than an opinion. Return the
  first run of hours under a stated rain threshold and say what the threshold
  was, instead of scoring hours against each other and hiding the rule in a
  magic number.

### 22. Meet in the middle

The geographic midpoint between two named places, and how far each person
travels.

- **Outcome** `meet.midpoint`
- **Inputs** `place_a` (string), `place_b` (string)
- **Outputs** `midpoint_name` (string), `latitude` (number), `longitude`
  (number), `distance_a_km` (number), `distance_b_km` (number),
  `total_km` (number)
- **Public API** Nominatim, no key, for geocoding both places and reverse
  geocoding the midpoint:
  `https://nominatim.openstreetmap.org/search?q=Bristol&format=json`
  `https://nominatim.openstreetmap.org/reverse?lat=52.1&lon=-1.9&format=json`
  It needs a descriptive `User-Agent` and allows about one request per second.
- **Hardest part** Three requests at one per second is most of your budget, so
  set a short timeout on each, and remember the midpoint of two places can land
  in a field — return the nearest named place from the reverse lookup and the
  two distances, which are the figures people actually want.

### 23. What was reported near here?

Street-level crime reported near a place in the most recent published month.

- **Outcome** `crime.nearby`
- **Inputs** `place_or_postcode` (string), `month` (string, optional, YYYY-MM)
- **Outputs** `total` (integer), `top_category` (string), `categories` (array
  of string), `month_used` (string), `place_used` (string)
- **Public API** data.police.uk, no key:
  `https://data.police.uk/api/crimes-street/all-crime?lat=51.5&lng=-0.13&date=2026-08`
  plus postcodes.io for coordinates, and
  `https://data.police.uk/api/crime-last-updated` for the month to ask for.
- **Hardest part** The lag. Measured on 2 November 2026 the latest published
  month was **August** — one to three months, not "roughly a month", so never
  guess it: call `/crime-last-updated` and return `month_used`. An unpublished
  month answers **404 with an empty body**, not an empty list. England, Wales
  and Northern Ireland only; a Scottish postcode geocodes fine and then has no
  crime data, which reads exactly like a safe street.
- **Watch the size.** One month of central London is **3,245 items and
  1.25 MB**. Aggregate to counts and return the top few; never the raw list.
  `outcome_known_percent` was listed here and is not worth it — it means
  walking `outcome_status` across thousands of records for a figure nobody
  asked for.

### 24. Turn leave into long weekends

Given a number of days of annual leave, find the arrangement that produces the
longest continuous break.

- **Outcomes** `holidays.upcoming` and `leave.optimise`
- **Inputs** `country` (string), `days_of_leave` (integer), `from_date`
  (string, optional)
- **Outputs** `best_start` (string), `best_end` (string), `total_days_off`
  (integer), `leave_used` (integer), `holidays_used` (array of string)
- **Public API** Nager.Date, no key:
  `https://date.nager.at/api/v3/PublicHolidays/2027/IE`
- **Hardest part** Not the search — that is a short loop over start dates. The
  trap is two outcomes whose example phrases overlap, which makes Pippa choose
  between them by guessing.

---

## A short list of free, no-key APIs

Useful if none of the above fits, or you want to swap the data source in an
idea you like. None of these needs an account.

| API | Base URL | What it gives you |
|---|---|---|
| Open-Meteo | `api.open-meteo.com/v1/forecast` | Weather, hourly and daily, worldwide |
| Open-Meteo geocoding | `geocoding-api.open-meteo.com/v1/search` | Place name to coordinates and time zone |
| Open-Meteo air quality | `air-quality-api.open-meteo.com/v1/air-quality` | Particulates and air quality index |
| Open-Meteo marine | `marine-api.open-meteo.com/v1/marine` | Wave height and sea surface temperature |
| Nominatim | `nominatim.openstreetmap.org/search` | Geocoding and reverse geocoding (needs a `User-Agent`) |
| postcodes.io | `api.postcodes.io/postcodes/SW1A1AA` | UK postcode to coordinates, council, ward |
| Nager.Date | `date.nager.at/api/v3/PublicHolidays/2026/GB` | Public holidays by country and year |
| Frankfurter | `api.frankfurter.app/latest` | Exchange rates, ECB reference |
| Environment Agency | `environment.data.gov.uk/flood-monitoring/id/floods` | England flood warnings and river levels |
| Carbon Intensity | `api.carbonintensity.org.uk/intensity` | GB grid carbon intensity, now and forecast |
| ~~TfL~~ | `api.tfl.gov.uk` | **Blocked — returns 403 `error code: 1010`. Do not plan around it.** |
| Deutsche Bahn (community) | `v6.db.transport.rest` | German rail departures and journeys |
| USGS | `earthquake.usgs.gov/earthquakes/feed/v1.0/summary/` | Earthquake feeds by magnitude and period |
| Hacker News | `hacker-news.firebaseio.com/v0/` | Stories, scores, comments |
| Sunrise Sunset | `api.sunrise-sunset.org/json` | Sunrise, sunset, twilight for coordinates |
| Wikimedia pageviews | `wikimedia.org/api/rest_v1/metrics/pageviews/` | Daily article view counts |
| Wikipedia REST | `en.wikipedia.org/api/rest_v1/page/summary/` | Article titles and summaries (needs a `User-Agent`) |
| Crossref | `api.crossref.org/works` | Papers, DOIs, citation counts |
| Open Food Facts | `world.openfoodfacts.org/api/v2/product/` | Food products by barcode, nutrition per 100 g |
| data.police.uk | `data.police.uk/api/crimes-street/all-crime` | UK street-level crime |
| Where the ISS at | `api.wheretheiss.at/v1/satellites/25544` | Space station position and altitude |
| NASA (demo key) | `api.nasa.gov/neo/rest/v1/feed?api_key=DEMO_KEY` | Near-earth asteroids. Keyed, but `DEMO_KEY` is public — 30 req/hour per IP, **shared** |

Two cautions. Check the terms of anything you use: most of these ask for a
descriptive `User-Agent` and polite request rates, and two of them refuse you
without one — **verified: Nominatim and Wikipedia/Wikimedia both return `403`
to a request with no `User-Agent`**, and Python sends no useful one by default.
Before you build on any source here, call it once by hand and look at what
comes back for a bad input: several of these answer **`200` with an empty
body** rather than an error, which is the failure most likely to reach a user
as a confident wrong answer. `docs/API_APPS.md` has the measured list. And prefer the sources whose numbers change, or that depend on
what the user said — a source of facts that never change usually means an app
Pippa will answer over.

---

## Ideas that will NOT work here

### Cannot be built under the rules

Each of these is a reasonable app in general. None of them can exist here, and
it is much cheaper to find that out now.

**"Read my email and tell me what needs a reply."**
Needs your Google or Microsoft account. That means a `connectors:` or
`secrets:` block in the manifest, and registration refuses any hackathon app
that declares either. The same applies to Slack, Notion, Spotify, Strava,
GitHub private repositories and your bank.

**"Add it to my calendar."**
Same reason, plus it writes somewhere. Your app is given its declared inputs
and nothing about the person: no user id, no account, no conversation history.

**"Track my water intake."** / **"Remember my team and tell me their score."**
Needs memory between calls. `persistence: none` is enforced, a new copy of your
app is built every time, and anything written last time is gone.

**"Keep a running leaderboard for the hackathon."**
Same reason. There is nowhere to put it.

**"Directions from A to B."**
Routing APIs that are any good need a paid key. Your repository is readable, so
a key pasted into the code is a key you have published. Use a free, no-key API,
or change the idea to something a free one answers — distance rather than
directions, for instance.

**"Scrape every listing on this site and compare them."**
Fifty sequential requests will not finish in twenty seconds. The call is killed
and the user is told the app failed.

**"Classify this photo."** / **"Run a sentiment model."**
Needs numpy, torch, transformers or similar. Only the Python 3.12 standard
library, `pippa_agentapp_sdk` and `PyYAML` are installed where your app runs,
so the import fails on the first call. Committing the library into the
repository does not help: the package must stay under 3 MB, and the build
refuses wheel files.

**"Use pandas to crunch the numbers."**
Same reason. `statistics`, `math` and a list comprehension cover almost
everything a hackathon app needs.

**"Ask the user a follow-up question, then answer."**
There is no conversation. One call in, one result out. Anything the app needs
has to be declared as an input; if it is missing, raise `AgentAppError` with a
`user_message` saying what was needed.

**"What's my name?"** / **"Where do I live?"**
Your app is told the inputs its manifest declares and nothing about who is
asking. There is no user identity in a call, on purpose — it is what makes an
app safe to run.

### Can be built, but will not be used

These all publish happily. Pippa then answers the question herself and your app
is never called. The run is green, the badge never appears, and there is
nothing to debug.

**"Translate this into Spanish."**
Pippa translates before an app is consulted.

**"Summarise this article."** / **"Rewrite this email politely."**
Your app returns structured data and Pippa writes the prose, so a paragraph is
not an app-shaped output — and she has already written it.

**"Write me a poem."** / **"Suggest a name for my cat."**
Generating text is the one thing an assistant does without help.

**"What does API stand for?"** / **"Define entropy."**
Definitions and acronyms are answered from memory.

**"Explain how a heat pump works."**
Same. An explanation is prose, and Pippa has one.

**"Which laptop should I buy?"** / **"Pick a restaurant for us."**
Choosing and opinions. If you want this shape to work, return the figures
instead — the price, the distance, the opening hours — and let Pippa do the
choosing out loud.

**"Who wrote Hamlet?"** / **"What is the capital of Peru?"**
General knowledge. Your app loses the routing contest every time.

If an idea you like is in this list, it can usually be moved one step to the
left: not "summarise the news", but "what are the top stories and their
scores"; not "which day should we meet", but "what is the forecast for each of
these three days".

---

## Before Claude starts building

Ask Claude to do these in order. It knows the order, but it helps if you do
too.

1. **The example phrases first** — five to ten, out loud, as a person would say
   them. If that is hard, change the idea.
2. **The `output` fields second.** If you cannot name them, nobody yet knows
   what the app returns.
3. **Then `app.py` and `test_app.py`.** Claude writes both.
4. **Then the push.** The build installs Python, checks the manifest, runs the
   tests and publishes. You run nothing.

If something goes wrong, tell Claude — it can read the build log and fix it.
`docs/TROUBLESHOOTING.md` lists the errors you are most likely to meet, with
the exact text.
