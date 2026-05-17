#!/usr/bin/env python3
"""
Build the static HTML site from content/*.md files.

Usage: python3 build.py

Outputs into site/. The 00-index.md becomes site/index.html.
Relative .md links are rewritten to .html.
"""

import json
import re
import shutil
import sys
from pathlib import Path

try:
    import markdown
except ImportError:
    sys.exit("Install markdown first: pip3 install --user markdown")

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"
PLACES = ROOT / "places"
GLOSSARY = ROOT / "glossary.json"
SITE = ROOT / "site"

HEADER_TITLE = "Japan — 40th Birthday Trip"
HEADER_SUBTITLE = "Oct 23 – Nov 6, 2026 · Clemens + Sonja"

# Each section: (label, [(file_stem, title), ...])
# file_stem = the markdown filename without extension; will be linked as .html
NAV_SECTIONS = [
    ("Start here", [
        ("01-overview", "Overview"),
        ("reservations", "Reservations checklist"),
        ("budget", "Budget per person"),
        ("19-foliage-timing", "Foliage timing"),
    ]),
    ("Tokyo (Days 1–5)", [
        ("day-01-tokyo", "Day 1 · Fri Oct 23"),
        ("day-02-tokyo", "Day 2 · Sat Oct 24"),
        ("day-03-tokyo", "Day 3 · Sun Oct 25"),
        ("day-04-tokyo-kamakura", "Day 4 · Mon Oct 26 — Kamakura"),
        ("day-05-tokyo", "Day 5 · Tue Oct 27"),
    ]),
    ("Hakone (Days 6–7)", [
        ("day-06-hakone", "Day 6 · Wed Oct 28"),
        ("day-07-hakone", "Day 7 · Thu Oct 29"),
    ]),
    ("Takayama (Days 8–10)", [
        ("day-08-takayama", "Day 8 · Fri Oct 30"),
        ("day-09-takayama", "Day 9 · Sat Oct 31"),
        ("day-10-takayama-shirakawago", "Day 10 · Sun Nov 1 — Shirakawa-go"),
    ]),
    ("Kyoto (Days 11–15)", [
        ("day-11-kyoto", "Day 11 · Mon Nov 2"),
        ("day-12-kyoto", "Day 12 · Tue Nov 3 — Ohara"),
        ("day-13-kyoto", "Day 13 · Wed Nov 4"),
        ("day-14-kyoto", "Day 14 · Thu Nov 5 — Saiho-ji"),
        ("day-15-kyoto-kix", "Day 15 · Fri Nov 6 — fly KIX"),
    ]),
    ("Hotels", [
        ("hotels-tokyo", "Tokyo"),
        ("hotels-hakone", "Hakone"),
        ("hotels-takayama", "Takayama"),
        ("hotels-kyoto", "Kyoto"),
    ]),
    ("Practical", [
        ("practical-general", "General — etiquette, cash, SIM"),
        ("practical-tokyo", "Tokyo"),
        ("practical-hakone", "Hakone"),
        ("practical-takayama", "Takayama"),
        ("practical-kyoto", "Kyoto"),
    ]),
    ("Pre-trip", [
        ("packing", "Packing list"),
        ("emergency", "Emergency / health"),
    ]),
]


def nav_html(current_stem: str | None) -> str:
    """Generate sidebar nav HTML, marking the current page as active."""
    parts = ['<nav class="sidebar" aria-label="Site navigation">']
    parts.append('<a href="index.html" class="brand">')
    parts.append(f'<span class="brand-title">{HEADER_TITLE}</span>')
    parts.append(f'<span class="brand-sub">{HEADER_SUBTITLE}</span>')
    parts.append('</a>')
    for section_label, items in NAV_SECTIONS:
        parts.append('<div class="nav-section">')
        parts.append(f'<h3>{section_label}</h3>')
        parts.append('<ul>')
        for stem, title in items:
            cls = ' class="active"' if stem == current_stem else ''
            parts.append(f'<li><a href="{stem}.html"{cls}>{title}</a></li>')
        parts.append('</ul>')
        parts.append('</div>')
    parts.append('</nav>')
    return "\n".join(parts)


def render_md(md_text: str) -> str:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "attr_list", "smarty"],
        output_format="html5",
    )
    html = md.convert(md_text)
    # Rewrite relative .md links to .html so navigation works in the built site.
    html = re.sub(r'href="([^"#]+)\.md(#[^"]+)?"', r'href="\1.html\2"', html)
    return html


def link_places(html: str, stem: str) -> tuple[str, int, list[str]]:
    """Auto-link bolded place names in the rendered HTML to Google Maps.
    Returns (linked_html, link_count, unmatched_names).
    A place is "linked" when its name appears as a substring inside any
    <strong>...</strong> tag — the markdown convention in these day files
    bolds every place name (sometimes alone, sometimes as part of a longer
    bold like '**12:00 — Lunch: Maisen Aoyama Honten**'). The whole
    <strong> block is wrapped in an anchor, so the link covers the full
    bolded run."""
    places_file = PLACES / f"{stem}.json"
    if not places_file.is_file():
        return html, 0, []
    data = json.loads(places_file.read_text(encoding="utf-8"))
    # Process longest names first so "Maisen Aoyama Honten" wraps before "Maisen".
    places = sorted(
        (p for p in data.get("places", []) if p.get("lat") is not None),
        key=lambda p: -len(p["name"]),
    )
    count = 0
    unmatched = []
    for p in places:
        url = f"https://www.google.com/maps/search/?api=1&query={p['lat']},{p['lng']}"
        # Variants: full name, then with parentheticals stripped.
        bare = re.sub(r"\s*\([^)]*\)", "", p["name"]).strip()
        variants = [p["name"]]
        if bare and bare != p["name"]:
            variants.append(bare)
        matched_any = False
        for variant in variants:
            # Match bare <strong>...VARIANT...</strong>. Already-wrapped strongs
            # carry a data-linked attribute and so don't match this pattern.
            pattern = re.compile(
                r"<strong>([^<]*?" + re.escape(variant) + r"[^<]*?)</strong>"
            )

            def replace(m, _var=variant, _url=url):
                nonlocal count
                count += 1
                return (
                    f'<a class="place-link" href="{_url}" target="_blank" '
                    f'rel="noopener noreferrer" title="Open {_var} in Google Maps">'
                    f'<strong data-linked>{m.group(1)}</strong></a>'
                )

            new_html, n = pattern.subn(replace, html)
            if n > 0:
                html = new_html
                matched_any = True
                break  # Don't try shorter variants once one matched.
        if not matched_any:
            unmatched.append(p["name"])
    # Strip the marker so the rendered HTML stays clean.
    html = html.replace("<strong data-linked>", "<strong>")
    return html, count, unmatched


def render_map(stem: str) -> str:
    """If places/<stem>.json exists, return HTML for an interactive Leaflet map.
    Returns empty string otherwise."""
    places_file = PLACES / f"{stem}.json"
    if not places_file.is_file():
        return ""
    data = json.loads(places_file.read_text(encoding="utf-8"))
    places = data.get("places", [])
    if not places:
        return ""
    map_id = f"map-{stem}"
    places_json = json.dumps(places)
    return f"""
<div id="{map_id}" class="day-map" aria-label="Map of places for this day"></div>
<p class="day-map-legend">Pins are numbered in schedule order. Bolded place names in the schedule below link to Google Maps. Tiles © OpenStreetMap.</p>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script>
(function() {{
    var places = {places_json};
    var map = L.map({map_id!r}, {{ scrollWheelZoom: false }});
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        maxZoom: 19,
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }}).addTo(map);
    var bounds = [];
    places.forEach(function(p, i) {{
        var icon = L.divIcon({{
            className: 'day-map-pin',
            html: String(i + 1),
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        }});
        var popup = '<b>' + (i + 1) + '. ' + p.name + '</b>';
        if (p.time) popup += '<br><small>' + p.time + (p.category ? ' · ' + p.category : '') + '</small>';
        if (p.notes) popup += '<small>' + p.notes + '</small>';
        L.marker([p.lat, p.lng], {{ icon: icon }}).addTo(map).bindPopup(popup);
        bounds.push([p.lat, p.lng]);
    }});
    if (bounds.length === 1) {{
        map.setView(bounds[0], 15);
    }} else {{
        map.fitBounds(bounds, {{ padding: [30, 30] }});
    }}
    map.on('click', function() {{ map.scrollWheelZoom.enable(); }});
    map.on('mouseout', function() {{ map.scrollWheelZoom.disable(); }});
}})();
</script>
"""


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<button class="nav-toggle" aria-label="Toggle navigation" onclick="document.body.classList.toggle('nav-open')">☰</button>
<button class="theme-toggle" aria-label="Toggle dark mode" onclick="(function(){{var b=document.body;b.classList.toggle('dark');try{{localStorage.setItem('theme',b.classList.contains('dark')?'dark':'light');}}catch(e){{}}}})()">◐</button>
<button class="glossary-toggle" aria-label="Toggle glossary" onclick="document.body.classList.toggle('glossary-open')">📖 Glossary</button>
{nav}
<main class="content">
{body}
</main>
<aside class="glossary" aria-label="Trip glossary">
    <div class="glossary-header">
        <strong>Glossary</strong>
        <button class="glossary-close" aria-label="Close glossary" onclick="document.body.classList.remove('glossary-open')">✕</button>
    </div>
    <input type="search" class="glossary-search" placeholder="Search… (e.g. onsen, ryokan, kaiseki)" autocomplete="off">
    <div class="glossary-list"></div>
</aside>
<script>
(function() {{
    try {{
        var saved = localStorage.getItem('theme');
        if (saved === 'dark') document.body.classList.add('dark');
        else if (!saved && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {{
            document.body.classList.add('dark');
        }}
    }} catch (e) {{}}
}})();
</script>
<script>
(function() {{
    var TERMS = {glossary_json};
    var list = document.querySelector('.glossary-list');
    var search = document.querySelector('.glossary-search');
    function escape(s) {{
        return String(s).replace(/[&<>"']/g, function(c) {{
            return {{ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }}[c];
        }});
    }}
    function render(filter) {{
        var q = (filter || '').trim().toLowerCase();
        var matches = TERMS.filter(function(t) {{
            if (!q) return true;
            if (t.term.toLowerCase().indexOf(q) !== -1) return true;
            if ((t.aliases || []).some(function(a) {{ return a.toLowerCase().indexOf(q) !== -1; }})) return true;
            if (t.def.toLowerCase().indexOf(q) !== -1) return true;
            return false;
        }});
        if (matches.length === 0) {{
            list.innerHTML = '<p class="glossary-empty">No matches. Try a shorter query.</p>';
            return;
        }}
        list.innerHTML = matches.map(function(t) {{
            var aliases = (t.aliases && t.aliases.length) ? ' <span class="glossary-aliases">' + escape(t.aliases.join(' · ')) + '</span>' : '';
            var cat = t.category ? '<span class="glossary-cat">' + escape(t.category) + '</span>' : '';
            return '<dl class="glossary-entry"><dt>' + escape(t.term) + aliases + cat + '</dt><dd>' + escape(t.def) + '</dd></dl>';
        }}).join('');
    }}
    render('');
    search.addEventListener('input', function(e) {{ render(e.target.value); }});
    // ESC closes the panel
    document.addEventListener('keydown', function(e) {{
        if (e.key === 'Escape' && document.body.classList.contains('glossary-open')) {{
            document.body.classList.remove('glossary-open');
        }}
    }});
}})();
</script>
</body>
</html>
"""


def extract_title(html: str, fallback: str) -> str:
    m = re.search(r"<h1[^>]*>(.+?)</h1>", html, re.DOTALL)
    if not m:
        return fallback
    text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return text or fallback


def main():
    if not CONTENT.is_dir():
        sys.exit(f"Content directory missing: {CONTENT}")
    SITE.mkdir(exist_ok=True)

    md_files = sorted(CONTENT.glob("*.md"))
    if not md_files:
        sys.exit(f"No markdown files found in {CONTENT}")

    # Load glossary once; inline into every page.
    if GLOSSARY.is_file():
        glossary_data = json.loads(GLOSSARY.read_text(encoding="utf-8"))
        glossary_terms = sorted(glossary_data.get("terms", []), key=lambda t: t["term"].lower())
        glossary_json = json.dumps(glossary_terms, ensure_ascii=False)
        print(f"Loaded glossary: {len(glossary_terms)} terms")
    else:
        glossary_json = "[]"

    # Copy static assets (CSS, future images/fonts) into site/
    if ASSETS.is_dir():
        for asset in ASSETS.iterdir():
            if asset.is_file():
                shutil.copy2(asset, SITE / asset.name)
                print(f"  asset: {asset.name}")

    print(f"Building {len(md_files)} pages into {SITE}/")
    for md_path in md_files:
        stem = md_path.stem
        if stem == "00-index":
            out_name = "index.html"
            active_stem: str | None = None
        else:
            out_name = f"{stem}.html"
            active_stem = stem

        body = render_md(md_path.read_text(encoding="utf-8"))
        body, link_count, unmatched = link_places(body, stem)
        map_html = render_map(stem)
        if map_html:
            # Insert the map right before the first <h2> (typically "## Schedule").
            # Falls back to appending to the start of the body if no <h2> exists.
            if "<h2" in body:
                body = body.replace("<h2", map_html + "\n<h2", 1)
            else:
                body = map_html + body
        title = extract_title(body, stem)
        # Page <title> tag = "<page title> — Japan Trip"
        if title.lower().startswith("japan"):
            page_title = title
        else:
            page_title = f"{title} — Japan Trip"

        page = PAGE_TEMPLATE.format(
            title=page_title,
            nav=nav_html(active_stem),
            body=body,
            glossary_json=glossary_json,
        )
        (SITE / out_name).write_text(page, encoding="utf-8")
        link_note = f"  [{link_count} place links"
        if unmatched:
            link_note += f", {len(unmatched)} unmatched: {', '.join(unmatched[:3])}{'…' if len(unmatched) > 3 else ''}"
        link_note += "]" if link_count or unmatched else ""
        print(f"  {md_path.name:42} → site/{out_name}{link_note if link_count or unmatched else ''}")

    print(f"\nDone. Open file://{(SITE / 'index.html').resolve()}")


if __name__ == "__main__":
    main()
