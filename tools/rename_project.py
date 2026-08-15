"""Rename the template and generate literal project-specific SC4 IDs."""

from __future__ import annotations

import argparse
import fnmatch
import re
from pathlib import Path


OLD_NAME = "SC4TemplateDll"
DIRECTOR_ID = "0xE5C2B9A7u"
PANEL_ID = "0xCA510001u"
PATTERNS = (
    "*.txt", "*.md", "*.json", "*.yml", "*.yaml", "*.cmake",
    "CMakeLists.txt", "*.cpp", "*.hpp", "*.h", "*.def", "*.ini",
)


def kebab_case(value: str) -> str:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", value).lower()


def project_id(value: str) -> int:
    hash_value = 2166136261
    for character in value.encode():
        hash_value = ((hash_value ^ character) * 16777619) & 0xFFFFFFFF
    return hash_value


def format_id(value: int) -> str:
    return f"0x{value:08X}u"


def matching_files(paths: list[Path]) -> list[Path]:
    files: set[Path] = set()
    for path in paths:
        if path.is_file():
            files.add(path)
        elif path.is_dir():
            files.update(
                candidate for candidate in path.rglob("*")
                if candidate.is_file()
                and any(fnmatch.fnmatch(candidate.name, pattern) for pattern in PATTERNS)
            )
    return sorted(files)


def write_text(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "project_name",
        help="C++ project name, for example SC4SeasonJumper",
    )
    args = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", args.project_name):
        parser.error("project_name must start with a letter and contain only letters, digits, or underscores")

    root = Path(__file__).resolve().parent.parent
    old_names = [] if args.project_name == OLD_NAME else [OLD_NAME]
    old_slugs = [kebab_case(name) for name in old_names]
    new_slug = kebab_case(args.project_name)

    for path in matching_files([
        root / ".github", root / "cmake", root / "dist", root / "src",
        root / "tools", root / "CMakeLists.txt", root / "CMakePresets.json",
        root / "README.md", root / "vcpkg.json",
    ]):
        if path == Path(__file__):
            continue
        content = path.read_text(encoding="utf-8")
        updated = content
        for old_name in old_names:
            updated = updated.replace(old_name, args.project_name)
        for old_slug in old_slugs:
            updated = updated.replace(old_slug, new_slug)
        if updated != content:
            write_text(path, updated)

    for directory in (root / "dist", root / "src" / "dll"):
        if not directory.is_dir():
            continue
        for path in list(directory.iterdir()):
            new_name = path.name
            for old_name in old_names:
                new_name = new_name.replace(old_name, args.project_name)
            if new_name != path.name:
                path.rename(path.with_name(new_name))

    director_file = next((root / "src" / "dll").glob("*Director.cpp"), None)
    if director_file:
        content = director_file.read_text(encoding="utf-8")
        director_value = project_id(args.project_name)
        content = content.replace(DIRECTOR_ID, format_id(director_value))
        content = content.replace(PANEL_ID, format_id(director_value ^ 0xCA510001))
        write_text(director_file, content)

    print(f"Renamed template identifiers to {args.project_name}")


if __name__ == "__main__":
    main()
