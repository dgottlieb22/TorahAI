"""Download texts from the Sefaria API.

Usage: python -m scripts.download_sefaria --collections tanakh,bavli
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://www.sefaria.org"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DELAY = 0.5

# Static book lists for Tanakh and Bavli (well-known, stable)
TANAKH_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "I Samuel", "II Samuel", "I Kings", "II Kings",
    "Isaiah", "Jeremiah", "Ezekiel",
    "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
    "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Psalms", "Proverbs", "Job", "Song of Songs", "Ruth", "Lamentations",
    "Ecclesiastes", "Esther", "Daniel", "Ezra", "Nehemiah",
    "I Chronicles", "II Chronicles",
]

BAVLI_TRACTATES = [
    "Berakhot", "Shabbat", "Eruvin", "Pesachim", "Yoma", "Sukkah",
    "Beitzah", "Rosh Hashanah", "Taanit", "Megillah", "Moed Katan",
    "Chagigah", "Yevamot", "Ketubot", "Nedarim", "Nazir", "Sotah",
    "Gittin", "Kiddushin", "Bava Kamma", "Bava Metzia", "Bava Batra",
    "Sanhedrin", "Makkot", "Shevuot", "Avodah Zarah", "Horayot",
    "Zevachim", "Menachot", "Chullin", "Bekhorot", "Arakhin", "Temurah",
    "Keritot", "Meilah", "Tamid", "Niddah",
]

ALL_COLLECTIONS = [
    "tanakh", "bavli", "mishneh_torah",
    "shulchan_arukh", "mishnah_berurah", "yerushalmi",
]

# Category paths to match in the table of contents for dynamic collections
TOC_CATEGORY_MATCHERS = {
    "mishneh_torah": lambda cats: "Mishneh Torah" in cats and "Halakhah" in cats,
    "shulchan_arukh": lambda cats: "Shulchan Arukh" in cats and "Halakhah" in cats,
    "mishnah_berurah": lambda cats: "Mishnah Berurah" in cats,
    "yerushalmi": lambda cats: "Yerushalmi" in cats and "Talmud" in cats,
}


def api_get(path: str, retries: int = 1) -> dict | list | None:
    """Fetch JSON from Sefaria API with retry."""
    url = BASE_URL + path
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TorahAI-Downloader/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            if attempt < retries:
                print(f"  Retry {url}: {e}")
                time.sleep(1)
            else:
                print(f"  FAILED {url}: {e}")
                return None


def get_shape(title: str) -> list | None:
    """Get the shape (section counts) for a book."""
    encoded = urllib.parse.quote(title, safe="")
    return api_get(f"/api/shape/{encoded}")


def fetch_section(ref: str) -> dict | None:
    """Fetch a single section with both source and translation."""
    encoded = urllib.parse.quote(ref, safe="")
    return api_get(f"/api/v3/texts/{encoded}?version=source,translation&return_format=text_only")


def extract_verses(data: dict, ref_prefix: str) -> list[dict]:
    """Extract verse-level entries from a v3 API response."""
    verses = []
    if not data or "versions" not in data:
        return verses

    he_text, en_text = [], []
    for v in data["versions"]:
        text = v.get("text", [])
        if v.get("language") == "he":
            he_text = text if isinstance(text, list) else [text]
        elif v.get("language") == "en":
            en_text = text if isinstance(text, list) else [text]

    # Flatten nested lists (some texts have nested structure)
    he_text = _flatten(he_text)
    en_text = _flatten(en_text)

    count = max(len(he_text), len(en_text))
    for i in range(count):
        he = he_text[i] if i < len(he_text) else ""
        en = en_text[i] if i < len(en_text) else ""
        if he or en:
            verses.append({
                "ref": f"{ref_prefix}:{i + 1}",
                "he": he if isinstance(he, str) else "",
                "en": en if isinstance(en, str) else "",
            })
    return verses


def _flatten(lst: list) -> list:
    """Flatten nested lists into a single list of strings."""
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(_flatten(item))
        else:
            result.append(item)
    return result


def download_book(title: str, category: str, section_refs: list[str]) -> dict:
    """Download all sections of a book and return the combined data."""
    all_verses = []
    for i, ref in enumerate(section_refs):
        print(f"    [{i + 1}/{len(section_refs)}] {ref}")
        data = fetch_section(ref)
        if data:
            verses = extract_verses(data, ref)
            all_verses.extend(verses)
        time.sleep(DELAY)
    return {"title": title, "category": category, "sections": all_verses}


def make_section_refs_from_shape(title: str, shape_data) -> list[str]:
    """Build section refs from shape API response."""
    refs = []
    if isinstance(shape_data, list) and len(shape_data) > 0:
        # Shape returns a list of section objects or a nested structure
        section = shape_data[0] if isinstance(shape_data[0], dict) else shape_data
        if isinstance(section, dict):
            chapters = section.get("section", [])
            if isinstance(chapters, list):
                for i, _ in enumerate(chapters):
                    refs.append(f"{title}.{i + 1}")
    if not refs:
        # Fallback: try treating shape_data as a flat list of counts
        if isinstance(shape_data, list):
            for i in range(len(shape_data)):
                refs.append(f"{title}.{i + 1}")
    return refs


def make_talmud_refs(title: str, shape_data) -> list[str]:
    """Build daf refs for Talmud tractates (2a, 2b, 3a, 3b, ...)."""
    refs = []
    # Shape for Talmud gives us the number of amudim (pages)
    length = 0
    if isinstance(shape_data, list) and len(shape_data) > 0:
        section = shape_data[0] if isinstance(shape_data[0], dict) else None
        if section:
            sec = section.get("section", [])
            length = len(sec) if isinstance(sec, list) else 0
        else:
            length = len(shape_data)

    if length == 0:
        # Fallback: try a reasonable range
        length = 200

    # Talmud pages: 2a, 2b, 3a, 3b, ... up to the length
    # Each daf has 2 amudim, starting from daf 2
    daf = 2
    amud = "a"
    for _ in range(length):
        refs.append(f"{title}.{daf}{amud}")
        if amud == "a":
            amud = "b"
        else:
            amud = "a"
            daf += 1
    return refs


def safe_filename(title: str) -> str:
    """Convert a book title to a safe filename."""
    return title.replace(" ", "_").replace(",", "").replace("/", "_") + ".json"


def save_book(book_data: dict, subdir: str = "") -> None:
    """Save book data to a JSON file."""
    out_dir = DATA_DIR / subdir if subdir else DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / safe_filename(book_data["title"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(book_data, f, ensure_ascii=False, indent=2)
    print(f"  Saved {path} ({len(book_data['sections'])} verses)")


def download_tanakh():
    """Download all Tanakh books."""
    print("\n=== Downloading Tanakh ===")
    for title in TANAKH_BOOKS:
        outpath = DATA_DIR / safe_filename(title)
        if outpath.exists():
            print(f"  Skipping {title} (already exists)")
            continue
        print(f"  Downloading {title}...")
        shape = get_shape(title)
        time.sleep(DELAY)
        if not shape:
            print(f"  Could not get shape for {title}, skipping")
            continue
        refs = make_section_refs_from_shape(title, shape)
        if not refs:
            print(f"  No sections found for {title}, skipping")
            continue
        book = download_book(title, "Tanakh", refs)
        save_book(book)


def download_bavli():
    """Download all Bavli tractates."""
    print("\n=== Downloading Bavli ===")
    for title in BAVLI_TRACTATES:
        outpath = DATA_DIR / safe_filename(title)
        if outpath.exists():
            print(f"  Skipping {title} (already exists)")
            continue
        print(f"  Downloading {title}...")
        shape = get_shape(title)
        time.sleep(DELAY)
        if not shape:
            print(f"  Could not get shape for {title}, skipping")
            continue
        refs = make_talmud_refs(title, shape)
        if not refs:
            print(f"  No sections found for {title}, skipping")
            continue
        book = download_book(title, "Bavli", refs)
        save_book(book)


def find_books_in_toc(toc: list, matcher, category_path: list | None = None) -> list[str]:
    """Recursively walk the TOC to find book titles matching a category predicate."""
    if category_path is None:
        category_path = []
    titles = []
    for node in toc:
        if isinstance(node, dict):
            cat = node.get("category", "")
            current_path = category_path + ([cat] if cat else [])
            # If this node has contents (subcategories or books), recurse
            if "contents" in node:
                titles.extend(find_books_in_toc(node["contents"], matcher, current_path))
            # If this is a leaf node (a book), check if it matches
            elif "title" in node and matcher(current_path):
                titles.append(node["title"])
    return titles


def download_toc_collection(collection_name: str, category_label: str, is_talmud: bool = False):
    """Download a collection discovered via the table of contents."""
    print(f"\n=== Downloading {category_label} ===")
    matcher = TOC_CATEGORY_MATCHERS.get(collection_name)
    if not matcher:
        print(f"  No matcher for {collection_name}")
        return

    print("  Fetching table of contents...")
    toc = api_get("/api/table-of-contents")
    time.sleep(DELAY)
    if not toc:
        print("  Failed to fetch TOC")
        return

    titles = find_books_in_toc(toc, matcher)
    print(f"  Found {len(titles)} books")

    for title in titles:
        outpath = DATA_DIR / safe_filename(title)
        if outpath.exists():
            print(f"  Skipping {title} (already exists)")
            continue
        print(f"  Downloading {title}...")
        shape = get_shape(title)
        time.sleep(DELAY)
        if not shape:
            print(f"  Could not get shape for {title}, skipping")
            continue
        if is_talmud:
            refs = make_talmud_refs(title, shape)
        else:
            refs = make_section_refs_from_shape(title, shape)
        if not refs:
            print(f"  No sections found for {title}, skipping")
            continue
        book = download_book(title, category_label, refs)
        save_book(book)


def main():
    parser = argparse.ArgumentParser(description="Download texts from Sefaria API")
    parser.add_argument(
        "--collections",
        default=",".join(ALL_COLLECTIONS),
        help=f"Comma-separated list of collections ({','.join(ALL_COLLECTIONS)})",
    )
    args = parser.parse_args()
    collections = [c.strip() for c in args.collections.split(",")]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Data directory: {DATA_DIR}")

    for col in collections:
        if col == "tanakh":
            download_tanakh()
        elif col == "bavli":
            download_bavli()
        elif col == "mishneh_torah":
            download_toc_collection("mishneh_torah", "Mishneh Torah")
        elif col == "shulchan_arukh":
            download_toc_collection("shulchan_arukh", "Shulchan Arukh")
        elif col == "mishnah_berurah":
            download_toc_collection("mishnah_berurah", "Mishnah Berurah")
        elif col == "yerushalmi":
            download_toc_collection("yerushalmi", "Yerushalmi", is_talmud=True)
        else:
            print(f"Unknown collection: {col}")

    print("\nDone!")


if __name__ == "__main__":
    main()
