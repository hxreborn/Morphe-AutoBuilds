#!/usr/bin/env python3
"""Generate release_notes.md listing what this build actually changed.

Run from the repo root in the release job. Sources, in order of preference:
  - ./release-apks/*.apk   freshly built this run -> the "Updated" section
  - manifest.json          full inventory (carried over + new) -> the details table

Reuses record_build.py's filename parsing so version/arch extraction stays in one
place (arch tokens like arm64-v8a contain "-v8a", so naive parsing is wrong).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from record_build import extract_version_from_filename, detect_arch_from_filename


def app_from_filename(apk_name: str, arch: str) -> str:
    """App token is everything before the '-{arch}-' marker in the filename."""
    stem = apk_name[:-4] if apk_name.lower().endswith(".apk") else apk_name
    marker = f"-{arch}-"
    idx = stem.find(marker)
    return stem[:idx] if idx > 0 else stem


def pretty(app: str) -> str:
    # ponytail: dumb title-case, no display-name map; add one if a name reads wrong.
    return app.replace("-", " ").replace("_", " ").title()


def parse_apk(apk_name: str) -> dict:
    arch = detect_arch_from_filename(apk_name)
    return {
        "app": app_from_filename(apk_name, arch),
        "version": extract_version_from_filename(apk_name),
        "arch": arch,
    }


def collect_updated(apk_dir: Path, patch_by_app: dict) -> list[dict]:
    """One row per app, arches merged: {app, version, arches[], patch}."""
    by_app: dict[tuple, dict] = {}
    for apk in sorted(apk_dir.glob("*.apk")):
        p = parse_apk(apk.name)
        key = (p["app"], p["version"])
        row = by_app.setdefault(key, {
            "app": p["app"], "version": p["version"],
            "arches": [], "patch": patch_by_app.get(p["app"], ""),
        })
        if p["arch"] not in row["arches"]:
            row["arches"].append(p["arch"])
    return sorted(by_app.values(), key=lambda r: r["app"])


def inventory_rows(manifest_path: Path) -> list[dict]:
    if not manifest_path.exists():
        return []
    try:
        entries = json.loads(manifest_path.read_text(encoding="utf-8")).get("entries", {})
    except Exception:
        return []
    rows = []
    for e in entries.values():
        version = (e.get("built_version") or "").strip() or extract_version_from_filename(e.get("apk", ""))
        rows.append({
            "app": e.get("app_name", ""),
            "version": version or "?",
            "arch": e.get("arch", "universal"),
            "patch": (e.get("patch_version") or "").strip(),
        })
    return sorted(rows, key=lambda r: (r["app"], r["arch"]))


def render(updated: list[dict], inventory: list[dict]) -> str:
    out: list[str] = []
    if updated:
        out.append(f"### Updated in this build ({len(updated)})\n")
        for r in updated:
            ver = f" `{r['version']}`" if r["version"] else ""
            patch = f" (patches `{r['patch']}`)" if r.get("patch") else ""
            out.append(f"- **{pretty(r['app'])}**{ver}{patch} — {', '.join(r['arches'])}")
        out.append("")

    out.append("Stock APKs patched with the latest Morphe bundles. Rebuilt daily at 06:00 UTC.")
    out.append("")
    out.append("`universal` runs on any ARM device, `arm64-v8a` only on 64-bit ones.")
    out.append("")

    if inventory:
        out.append("<details><summary>All apps in this release</summary>\n")
        out.append("| App | Version | Patches | Arch |")
        out.append("|-----|---------|---------|------|")
        for r in inventory:
            out.append(f"| {pretty(r['app'])} | {r['version']} | {r['patch'] or '—'} | {r['arch']} |")
        out.append("\n</details>")
        out.append("")

    out.append("Built automatically. Use at your own risk.")
    return "\n".join(out) + "\n"


def _selftest() -> None:
    p = parse_apk("youtube-music-arm64-v8a-hxreborn-v8.29.53.apk")
    assert p == {"app": "youtube-music", "version": "8.29.53", "arch": "arm64-v8a"}, p
    p = parse_apk("showly-universal-hxreborn-v1.2.3.apk")
    assert p == {"app": "showly", "version": "1.2.3", "arch": "universal"}, p
    md = render(
        [{"app": "tiktok", "version": "43.8.3", "arches": ["arm64-v8a"], "patch": "0.4.0"}],
        [{"app": "tiktok", "version": "43.8.3", "arch": "arm64-v8a", "patch": "0.4.0"}],
    )
    assert "**Tiktok** `43.8.3` (patches `0.4.0`) — arm64-v8a" in md, md
    assert "| Tiktok | 43.8.3 | 0.4.0 | arm64-v8a |" in md, md
    print("selftest ok")


def main() -> int:
    if "--selftest" in sys.argv:
        _selftest()
        return 0
    inventory = inventory_rows(Path("manifest.json"))
    patch_by_app = {r["app"]: r["patch"] for r in inventory if r["patch"]}
    updated = collect_updated(Path("release-apks"), patch_by_app)
    Path("release_notes.md").write_text(render(updated, inventory), encoding="utf-8")
    print(f"Wrote release_notes.md ({len(updated)} updated, {len(inventory)} in inventory)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
