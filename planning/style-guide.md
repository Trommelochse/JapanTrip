# Style Guide for Phase 2 Research Agents

Every per-stop research agent MUST follow this guide. Produces consistent output across the four stops so assembly is painless.

## Required reading before drafting

1. `planning/preferences.md` — travel preferences and hard rules (no alcohol, wander time, depth, off-path)
2. `planning/route.md` — locked dates, locked skeleton, Phase 2 day assignments
3. This file

## Output location

Each agent writes Markdown files into `content/`:
- One file per day: `content/day-01-tokyo.md`, `content/day-02-tokyo.md`, etc.
- One **hotel picks** file per stop: `content/hotels-tokyo.md`, `content/hotels-hakone.md`, etc.
- Append city-specific notes to `content/practical-<city>.md` if any are worth surfacing (transit cards, neighborhood overview).

## Day file template (mandatory)

Each day file uses this exact structure:

```markdown
# Day N — [Weekday, Date] — [City]

> **Theme:** [one-line theme of the day]
> **Weather (typical):** [°C range, dry/rainy probability for the date]
> **Walking:** [low / medium / high — and rough km]

## Schedule

### Morning
- **HH:MM** — [activity / location] · [duration] · [transit note if relevant]
- **HH:MM** — [activity] · [duration]
- **HH:MM** — Lunch: [restaurant name + neighborhood] · [why this pick] · [reservation needed? cash only? hours?]

### Afternoon
- **HH:MM–HH:MM** — **Wander block** in [neighborhood] · [what's around: shops / cafés / vibe] · [optional split: Sonja → X, Clemens → Y]
- **HH:MM** — [activity]
- **HH:MM** — Snack / coffee: [kissaten or specialty coffee spot]

### Evening
- **HH:MM** — Dinner: [restaurant + neighborhood] · [why this pick] · [reservation status]
- **HH:MM** — [optional late activity, OR explicit "free evening — head back at your own pace"]

## Rain plan B
If it rains, swap [outdoor activity] for [indoor alternative + why]. Brief — 2-3 lines.

## Photography golden hour
- **Sunrise (~HH:MM):** [best spot if relevant]
- **Sunset (~HH:MM):** [best spot]
- [1-2 specific shot suggestions if there's an iconic frame]

## Reservations needed for this day
- [Thing] — book [when] via [how]
- (omit section if none)

## Off-path notes
- [1-3 bullets of specific, opinionated picks that aren't on the standard tourist list — could be a hidden coffee shop, a backstreet, a niche museum, a J-beauty boutique for Sonja]
```

## Hotel picks file template

`content/hotels-<city>.md`:

```markdown
# Hotels — [City]

For nights [start date] – [end date].

## Budget — €60–110 / night
**[Hotel name]** · [neighborhood] · [link to booking]
- Why this pick: [1-2 sentences]
- Room type for two: [twin / double / capsule+] · ¥XX,XXX (~€XX) as of [date checked]
- Catch: [anything to know — small rooms, no English at front desk, etc.]

(repeat for 1-2 budget picks)

## Mid — €130–230 / night
**[Hotel name]** · [neighborhood] · [link]
- (same structure)

## Splurge — €280+ / night
**[Hotel name]** · [neighborhood] · [link]
- (same structure)

## My pick
[Which one I'd actually book and why, in 2-3 sentences. Be opinionated.]
```

**Hakone hotels file is special:** all three tiers are ryokan picks (no business hotels). Clemens has explicitly stated this is the splurge moment — exclude budget tiers but recommend a high-mid tier and 2 splurge tiers.

## Voice rules

- **Opinionated, not encyclopedic.** "Skip Tokyo Skytree — Tokyo City View at Roppongi is better and quieter" beats "Tokyo Skytree is a popular observation deck."
- **Concrete, not generic.** Names, addresses, prices, hours, train lines. No "many great restaurants in the area."
- **Off-path for restaurants.** Hard rule: NO Ichiran, Ippudo, Tsuta, Afuri, anything on TikTok / "10 best Tokyo" lists. Local-favorite or genuinely obscure. If a place is famous (e.g. Sushi Saito), say so and offer a less-famous-equivalent.
- **No alcohol framing.** Don't describe a place as "great for drinks." Yakitori spots are fine if framed around the food.
- **Wander time is sacred.** Every day has at least one labeled "Wander block" of 2–3h in the schedule. Don't bury it as "free time" in a footnote.
- **Respect the user's stated splurge ceiling.** One Hakone ryokan splurge for the trip. Don't propose additional luxury moments elsewhere unless asked.

## Sourcing & reliability rules

- Every hotel price and booking link must be **verified via WebSearch / WebFetch on the day of drafting.** Note the check date in the file.
- Every restaurant must have **address + verified opening hours + verified day-closed**. Many small Tokyo / Kyoto spots close 1–2 days a week; getting the day wrong wastes a meal.
- Every reservation deadline must cite an authoritative source (the temple/restaurant's own page, or a recently-dated travel-blog post).
- **No hallucinated phone numbers, no made-up addresses.** If you can't verify, leave the field blank and note "verify before booking."
- Prefer official sites and Japan-based aggregators (Tabelog, Jalan, official tourism boards) over English travel blogs for primary facts.

## What NOT to do

- Don't recommend the JR Pass (no longer worth it for this itinerary — see draft.md).
- Don't include alcohol-centric recommendations of any kind.
- Don't over-pack the schedule. If you find yourself listing >5 activities/day, cut.
- Don't list hotels you can't get a current price for. Better 2 verified picks than 3 with one stale.
- Don't recommend Ichiran, Ippudo, Tsuta, Afuri, Hot Pepper-top-10 ramen, or anything with a 30+ minute line of foreign tourists.
- Don't write filler. Every sentence earns its place.
- Don't create files outside `content/` unless you have a strong reason — flag it in your response instead.

## File naming convention

```
content/
  day-01-tokyo.md
  day-02-tokyo.md
  day-03-tokyo.md
  day-04-tokyo-kamakura.md
  day-05-tokyo.md
  day-06-hakone.md
  day-07-hakone.md
  day-08-takayama.md
  day-09-takayama.md
  day-10-takayama-shirakawago.md
  day-11-kyoto.md
  day-12-kyoto.md
  day-13-kyoto.md
  day-14-kyoto.md
  day-15-kyoto-kix.md
  hotels-tokyo.md
  hotels-hakone.md
  hotels-takayama.md
  hotels-kyoto.md
  practical-tokyo.md      (optional, only if notes are city-specific and worth surfacing)
  practical-hakone.md     (optional)
  practical-takayama.md   (optional)
  practical-kyoto.md      (optional)
```

Index file (`content/00-index.md`) and cross-cutting files (packing, emergency, reservations) are produced by the assembly phase, not the per-stop agents.
