import json
import re
from pathlib import Path

_STRIP_HTML = re.compile(r"<[^>]+>")

TORAH = {"Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"}
PROPHETS = {
    "Joshua", "Judges", "I Samuel", "II Samuel", "I Kings", "II Kings",
    "Isaiah", "Jeremiah", "Ezekiel", "Hosea", "Joel", "Amos", "Obadiah",
    "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
    "Zechariah", "Malachi",
}
WRITINGS = {
    "Psalms", "Proverbs", "Job", "Song of Songs", "Ruth", "Lamentations",
    "Ecclesiastes", "Esther", "Daniel", "Ezra", "Nehemiah",
    "I Chronicles", "II Chronicles",
}
TANACH = TORAH | PROPHETS | WRITINGS

BAVLI_TRACTATES = {
    "Berakhot", "Shabbat", "Eruvin", "Pesachim", "Yoma", "Sukkah",
    "Beitzah", "Rosh Hashanah", "Taanit", "Megillah", "Moed Katan",
    "Chagigah", "Yevamot", "Ketubot", "Nedarim", "Nazir", "Sotah",
    "Gittin", "Kiddushin", "Bava Kamma", "Bava Metzia", "Bava Batra",
    "Sanhedrin", "Makkot", "Shevuot", "Avodah Zarah", "Horayot",
    "Zevachim", "Menachot", "Chullin", "Bekhorot", "Arakhin", "Temurah",
    "Keritot", "Meilah", "Tamid", "Niddah",
}


def _clean(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""
    return _STRIP_HTML.sub("", text).strip()


def _infer_category(book: str) -> str:
    if book in TANACH:
        return "Tanach"
    if "Talmud" in book or book in BAVLI_TRACTATES:
        return "Bavli"
    return "Other"


def _flatten_text(nested, book: str) -> list[tuple[str, str]]:
    """Flatten nested lists into (ref, text) pairs."""
    results = []
    if not isinstance(nested, list):
        return results
    for ch_idx, chapter in enumerate(nested, start=1):
        if isinstance(chapter, list):
            for v_idx, verse in enumerate(chapter, start=1):
                ref = f"{book} {ch_idx}:{v_idx}"
                results.append((ref, _clean(verse)))
        elif isinstance(chapter, str):
            ref = f"{book} {ch_idx}"
            results.append((ref, _clean(chapter)))
    return results


def parse_sefaria_file(filepath: str) -> list[dict]:
    path = Path(filepath)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # --- New v3 API download format ---
    if "sections" in data:
        book = data.get("title", path.stem)
        category = data.get("category") or _infer_category(book)
        return [
            {
                "ref": s["ref"],
                "book": book,
                "text_he": _clean(s.get("he", "")),
                "text_en": _clean(s.get("en", "")),
                "category": category,
            }
            for s in data["sections"]
            if _clean(s.get("he", ""))
        ]

    # --- Legacy Sefaria export format ---
    book = path.stem
    category = _infer_category(book)

    he_pairs = _flatten_text(data.get("text", []), book)

    en_raw = data.get("text_en") or data.get("en", [])
    en_pairs = _flatten_text(en_raw, book) if en_raw else []
    en_map = dict(en_pairs)

    entries = []
    for ref, text_he in he_pairs:
        if not text_he:
            continue
        entries.append({
            "ref": ref,
            "book": book,
            "text_he": text_he,
            "text_en": en_map.get(ref, ""),
            "category": category,
        })
    return entries
