import argparse
import os
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract Item name and description attributes from XML files "
            "and emit an i18n XML file."
        )
    )
    parser.add_argument(
        "base_dir",
        help="Root directory to scan for XML files.",
    )
    parser.add_argument(
        "output_file",
        help="Destination path for the generated localisation XML.",
    )
    return parser.parse_args()


def collect_entries(base_dir: str) -> dict:
    entries = {}
    for root, dirs, files in os.walk(base_dir):
        rel_root = os.path.relpath(root, base_dir)
        if rel_root == "i18n" or rel_root.startswith("i18n" + os.sep):
            continue
        for fname in files:
            if not fname.lower().endswith(".xml"):
                continue
            path = os.path.join(root, fname)
            rel_path = os.path.relpath(path, base_dir).replace("\\", "/")
            if rel_path.startswith("i18n/"):
                continue
            try:
                tree = ET.parse(path)
            except ET.ParseError:
                continue
            for elem in tree.iter():
                if elem.tag.lower() != "item":
                    continue
                identifier = elem.attrib.get("identifier")
                if not identifier:
                    continue
                entry = entries.setdefault(
                    identifier,
                    {
                        "name": None,
                        "name_paths": set(),
                        "description": None,
                        "description_paths": set(),
                    },
                )
                name = elem.attrib.get("name")
                if name:
                    if entry["name"] is None:
                        entry["name"] = name
                    entry["name_paths"].add(rel_path)
                description = elem.attrib.get("description")
                if description:
                    if entry["description"] is None:
                        entry["description"] = description
                    entry["description_paths"].add(rel_path)
    return entries


def build_output(entries: dict) -> str:
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<infotexts language="English" nowhitespace="false" translatedname="English">',
        "  <!-- Items -->",
    ]

    for identifier in sorted(entries):
        entry = entries[identifier]
        if entry["name"]:
            paths = ", ".join(sorted(entry["name_paths"]))
            comment = f'  <!-- {paths} : Item identifier="{identifier}" name -->'
            lines.append(comment)
            lines.append(
                f'  <entityname.{identifier}>{escape(entry["name"])}</entityname.{identifier}>'
            )
        if entry["description"]:
            paths = ", ".join(sorted(entry["description_paths"]))
            comment = f'  <!-- {paths} : Item identifier="{identifier}" description -->'
            lines.append(comment)
            lines.append(
                f'  <entitydescription.{identifier}>{escape(entry["description"])}</entitydescription.{identifier}>'
            )

    lines.append("</infotexts>")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    base_dir = os.path.abspath(args.base_dir)
    output_path = os.path.abspath(args.output_file)

    entries = collect_entries(base_dir)
    output = build_output(entries)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as outfile:
        outfile.write(output)


if __name__ == "__main__":
    main()
