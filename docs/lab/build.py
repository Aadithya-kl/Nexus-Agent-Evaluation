"""Build the self-contained browser lab from repository sources."""

import argparse
import json
from pathlib import Path

LAB = Path(__file__).resolve().parent
REPO = LAB.parents[1]


def render() -> bytes:
    fixtures = {
        key: json.loads((REPO / "examples" / filename).read_text(encoding="utf-8"))
        for key, filename in {
            "cases": "cases.json",
            "predictions": "predictions.json",
            "rejected": "rejected-predictions.json",
        }.items()
    }
    template = (LAB / "template.html").read_text(encoding="utf-8")
    engine = (LAB / "engine.js").read_text(encoding="utf-8")
    license_text = (REPO / "LICENSE").read_text(encoding="utf-8")
    fixture_json = json.dumps(fixtures, ensure_ascii=True).replace("<", "\\u003c")
    html = (
        template.replace("/*ENGINE*/", engine, 1)
        .replace("/*FIXTURES*/", fixture_json, 1)
        .replace("<!doctype html>", f"<!doctype html>\n<!--\n{license_text}-->\n", 1)
    )
    return html.encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check the committed HTML")
    args = parser.parse_args()
    output = LAB / "index.html"
    rendered = render()
    if args.check:
        if not output.is_file() or output.read_bytes() != rendered:
            parser.error("index.html is stale. Run python docs/lab/build.py.")
        print("index.html matches the reproducible build")
    else:
        output.write_bytes(rendered)


if __name__ == "__main__":
    main()
