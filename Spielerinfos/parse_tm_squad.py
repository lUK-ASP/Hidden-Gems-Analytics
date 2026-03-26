import re
import csv
from pathlib import Path
from typing import List, Dict, Optional

from bs4 import BeautifulSoup


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def normalize_escaped_html(raw: str) -> str:
    raw = raw.replace("\\\r\n", "\n").replace("\\\n", "\n")
    raw = re.sub(r"\\'([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), raw)
    return raw.encode("latin-1", "ignore").decode("cp1252", "ignore")


def parse_market_value(text: str) -> Optional[int]:
    t = clean(text).replace("€", "").replace("Mio.", "Mio").replace("Tsd.", "Tsd")
    t = t.replace(".", "").replace(",", ".").strip()
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(Mio|Tsd)$", t, re.IGNORECASE)
    if not m:
        return None
    val, unit = float(m.group(1)), m.group(2).lower()
    return int(round(val * (1_000_000 if unit == "mio" else 1_000)))


def extract_nationalities(cell) -> List[str]:
    titles = (clean(img.get("title") or img.get("alt", "")) for img in cell.select("img"))
    return list(dict.fromkeys(t for t in titles if t))


def find_table_items(html: str):
    soup = BeautifulSoup(html, "lxml")
    if table := soup.select_one("table.items"):
        return table

    if m := re.search(r'(<table[^>]*class="[^"]*\bitems\b[^"]*".*?</table>)', html, re.I | re.S):
        return BeautifulSoup(m.group(1), "lxml").find("table")

    if "<tbody" in html and "<tr" in html:
        return BeautifulSoup(f"<table class='items'>{html}</table>", "lxml").select_one("table.items")

    return None


def parse_team_html(html: str) -> List[Dict]:
    table = find_table_items(html)
    if not table:
        raise ValueError("Keine 'table.items' gefunden.")

    players = []
    for tr in table.select("tbody > tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 4:
            continue

        player_cell = tds[1]
        name_tag = (
            player_cell.select_one("td.hauptlink a")
            or player_cell.select_one("a[href*='/profil/spieler/']")
        )
        pos_tag = player_cell.select_one("table.inline-table tr:nth-of-type(2) td")

        dob_age = clean(tds[2].get_text(" ", strip=True))
        dob_m = re.search(r"(\d{2}\.\d{2}\.\d{4})", dob_age)
        dob = dob_m.group(1) if dob_m else None
        age = int(m.group(1)) if (m := re.search(r"\((\d{1,2})\)", dob_age)) else None

        marktwert_text = clean(tds[-1].get_text(" ", strip=True))
        maybe_contract = clean(tds[-2].get_text(" ", strip=True)) if len(tds) >= 2 else ""
        vertrag_bis = maybe_contract if re.match(r"^\d{2}\.\d{2}\.\d{4}$", maybe_contract) else None

        # Heuristiken: Größe, Fuß, im_team_seit, vorheriger_verein
        groesse = fuss = im_team_seit = vorheriger_verein = None
        for td in tds:
            txt = clean(td.get_text(" ", strip=True))
            groesse = groesse or (txt if re.match(r"^\d,\d{2}m$", txt) else None)
            fuss = fuss or (txt if txt in {"rechts", "links", "beidfüßig"} else None)
            if not im_team_seit and re.match(r"^\d{2}\.\d{2}\.\d{4}$", txt) and txt not in {dob, vertrag_bis}:
                im_team_seit = txt

        for td in reversed(tds[:-1]):
            if img := td.select_one("img"):
                if title := clean(img.get("title") or img.get("alt") or ""):
                    vorheriger_verein = title
                    break

        players.append({
            "nummer":           clean(tds[0].get_text(" ", strip=True)) or None,
            "name":             clean(name_tag.get_text(" ", strip=True)) if name_tag else None,
            "position":         clean(pos_tag.get_text(" ", strip=True)) if pos_tag else None,
            "geburtsdatum":     dob,
            "alter":            age,
            "nationalitaeten":  ";".join(extract_nationalities(tds[3])) or None,
            "groesse":          groesse,
            "fuss":             fuss,
            "im_team_seit":     im_team_seit,
            "vorheriger_verein": vorheriger_verein,
            "vertrag_bis":      vertrag_bis,
            "marktwert_text":   marktwert_text or None,
            "marktwert_eur":    parse_market_value(marktwert_text),
        })

    return players


def read_dump_file(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if raw.lstrip().startswith("{\\rtf"):
        raw = raw[raw.find("<"):]
    is_escaped = any(x in raw for x in ("\\'", "\\\n", "\\\r\n"))
    return normalize_escaped_html(raw) if is_escaped else raw


def main():
    base_dir, out_dir = Path("data_html"), Path("output")
    out_dir.mkdir(exist_ok=True)

    all_files = sorted(base_dir.rglob("*.html")) + sorted(base_dir.rglob("*.txt"))
    if not all_files:
        print("❌ Keine Dateien gefunden in data_html/** (erwartet .html oder .txt).")
        return

    cols = [
        "saison", "team", "nummer", "name", "position", "geburtsdatum", "alter",
        "nationalitaeten", "groesse", "fuss", "im_team_seit", "vorheriger_verein",
        "vertrag_bis", "marktwert_text", "marktwert_eur",
    ]
    out_path = out_dir / "bundesliga.csv"

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()

        for file_path in all_files:
            saison, team = file_path.parent.name, file_path.stem
            try:
                rows = parse_team_html(read_dump_file(file_path))
            except Exception as e:
                print(f"❌ FEHLER bei {file_path}: {type(e).__name__}: {e}")
                print("   start:", file_path.read_text(encoding="utf-8", errors="ignore")[:200].replace("\n", " "))
                continue

            for r in rows:
                writer.writerow({c: {**r, "team": team, "saison": saison}.get(c) for c in cols})
            print(f"✅ {saison} / {team}: {len(rows)} Spieler")

    print(f"\n🎉 Fertig! CSV gespeichert: {out_path.resolve()}")


if __name__ == "__main__":
    main()
