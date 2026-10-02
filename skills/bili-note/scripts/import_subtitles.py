"""Import externally-exported Bilibili subtitles into bili-note's pipeline.

This bridges the bilibili-subtitle / vCaptions browser extension (or any tool
that exports standard SRT/VTT) into bili-note. The extension runs in the user's
browser and can download subtitles that the server-side API route cannot reach
(e.g. some AI-subtitle pages). This script turns that export into bili-note's
extraction layout and then delegates to archive_bili_materials.py so the full
archive, evidence indexes and note_budget.json are produced exactly as if the
agent had fetched the subtitles itself.

Only the Python standard library is used. No third-party dependencies.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


configure_stdout()


CUE_RE = re.compile(
    r"^\s*(?:\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{1,3}\s*-->\s*(?:\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{1,3}"
)
# Non-capturing group so findall returns the full timestamp tokens.
TS_TOKEN_RE = re.compile(r"(?:\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{1,3}")
# VTT comment / header markers that must never enter subtitle content.
NOTE_RE = re.compile(r"^\s*(NOTE|STYLE|REGION|WEBVTT)\b", re.IGNORECASE)


def parse_timestamp(token: str) -> float | None:
    token = token.strip()
    m = re.match(r"^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})[.,](\d{1,3})$", token)
    if not m:
        return None
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2))
    seconds = int(m.group(3))
    frac = m.group(4)
    frac_seconds = int(frac) / (10 ** len(frac))
    return hours * 3600 + minutes * 60 + seconds + frac_seconds


def parse_cues(text: str) -> list[dict[str, Any]]:
    """Parse SRT or VTT text into a list of {from, to, content} cues.

    The format (SRT vs VTT) is detected automatically by the timestamp
    pattern, so both are handled identically here.
    """
    lines = text.splitlines()
    cues: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_note = False
    for line in lines:
        if NOTE_RE.match(line):
            in_note = True
            continue
        if CUE_RE.match(line):
            in_note = False
            if current is not None:
                cues.append(current)
            times = TS_TOKEN_RE.findall(line)
            if len(times) < 2:
                current = None
                continue
            t0 = parse_timestamp(times[0])
            t1 = parse_timestamp(times[1])
            if t0 is None or t1 is None:
                current = None
                continue
            current = {"from": t0, "to": t1, "content": []}
        elif current is not None and not in_note:
            current["content"].append(line)
    if current is not None:
        cues.append(current)

    result: list[dict[str, Any]] = []
    for cue in cues:
        content = "\n".join(cue["content"]).strip()
        if not content:
            continue
        result.append({"from": cue["from"], "to": cue["to"], "content": content})
    return result


def fmt_srt_time(seconds: float) -> str:
    total = int(round(seconds * 1000))
    ms = total % 1000
    total //= 1000
    ss = total % 60
    total //= 60
    mm = total % 60
    hh = total // 60
    return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"


def build_srt(segs: list[dict[str, Any]]) -> str:
    out: list[str] = []
    for idx, seg in enumerate(segs, 1):
        out.append(str(idx))
        out.append(f"{fmt_srt_time(seg['from'])} --> {fmt_srt_time(seg['to'])}")
        out.append(seg["content"])
        out.append("")
    return "\n".join(out) + "\n"


def clean_filename(value: str, limit: int = 40) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value).strip(" ._")
    return (value[:limit] or "untitled").strip(" ._")


def load_archive_module(archive_script: Path):
    spec = importlib.util.spec_from_file_location("bili_note_archive", archive_script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load archive module from {archive_script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import externally-exported SRT/VTT subtitles into bili-note's archive pipeline."
    )
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="One or more .srt/.vtt files exported from the bilibili-subtitle extension (one per video part).",
    )
    parser.add_argument("--bvid", help="BVID of the source video, used for archive metadata.")
    parser.add_argument(
        "--part",
        help="Part/title label applied to all imported files (default: each file's stem).",
    )
    parser.add_argument(
        "--cid",
        help="Optional cid label applied to all imported files (default: ext<page>).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        help="Override total duration (seconds) per part; otherwise derived from the last cue timestamp.",
    )
    parser.add_argument(
        "--extract-dir",
        help="Temporary extraction directory. Default: a temp folder next to --archive-dir.",
    )
    parser.add_argument(
        "--archive-dir",
        required=True,
        help="Final archive directory (receives subtitles/indexes/metadata/README).",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Only build the extraction layout; skip archive_bili_materials.py.",
    )
    args = parser.parse_args()

    archive_dir = Path(args.archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)

    if args.extract_dir:
        extract_dir = Path(args.extract_dir)
    else:
        extract_dir = archive_dir.parent / f".import_tmp_{args.bvid or 'subtitles'}"
    extract_dir.mkdir(parents=True, exist_ok=True)
    (extract_dir / "subtitles" / "srt").mkdir(parents=True, exist_ok=True)
    (extract_dir / "subtitles" / "txt").mkdir(parents=True, exist_ok=True)
    (extract_dir / "subtitles" / "json").mkdir(parents=True, exist_ok=True)

    outputs: list[dict[str, Any]] = []
    page = 1
    for in_path in args.input:
        p = Path(in_path)
        if not p.is_file():
            print(f"WARN: input not found, skipped: {p}", file=sys.stderr)
            continue
        text = p.read_text(encoding="utf-8")
        segs = parse_cues(text)
        if not segs:
            print(f"WARN: no cues parsed from {p}, skipped", file=sys.stderr)
            continue

        part = args.part or p.stem
        cid = args.cid or f"ext{page}"
        stem = f"p{page:02d}_{cid}_{clean_filename(part, 40)}"

        srt_path = extract_dir / "subtitles" / "srt" / f"{stem}.srt"
        txt_path = extract_dir / "subtitles" / "txt" / f"{stem}.txt"
        json_path = extract_dir / "subtitles" / "json" / f"{stem}.subtitle.json"

        srt_path.write_text(build_srt(segs), encoding="utf-8")
        txt_path.write_text("\n".join(seg["content"] for seg in segs), encoding="utf-8")
        json_path.write_text(
            json.dumps(
                {
                    "body": [
                        {"from": seg["from"], "to": seg["to"], "content": seg["content"]}
                        for seg in segs
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        duration = args.duration or max((seg["to"] for seg in segs), default=0.0)
        outputs.append(
            {
                "page": page,
                "cid": cid,
                "part": part,
                "duration": round(duration, 3),
                "files": {
                    "txt": str(txt_path),
                    "srt": str(srt_path),
                    "json": str(json_path),
                },
                "source": "external_srt_vtt_import",
            }
        )
        print(
            f"imported {p.name}: {len(segs)} cues, "
            f"{round(duration)}s -> {stem}"
        )
        page += 1

    if not outputs:
        print("ERROR: no subtitles were imported", file=sys.stderr)
        return 1

    manifest = {
        "source": "external_srt_vtt_import",
        "bvid": args.bvid,
        "aid": None,
        "parts": len(outputs),
        "outputs": outputs,
    }
    (extract_dir / "subtitle_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if args.no_archive:
        print(f"extraction layout written to: {extract_dir}")
        return 0

    archive_script = Path(__file__).resolve().parent / "archive_bili_materials.py"
    if not archive_script.is_file():
        print(
            f"ERROR: archive_bili_materials.py not found at {archive_script}; "
            "cannot finalize archive. Use --no-archive to keep the extraction layout.",
            file=sys.stderr,
        )
        return 1

    archive_mod = load_archive_module(archive_script)
    metadata_info = archive_mod.archive_metadata(extract_dir, archive_dir)
    subtitle_info = archive_mod.archive_subtitles(extract_dir, archive_dir)
    article_info = archive_mod.archive_articles(extract_dir, archive_dir)
    comment_info = archive_mod.archive_comments(extract_dir, archive_dir)
    evidence_count = archive_mod.combine_evidence_indexes(archive_dir)
    note_budget = archive_mod.write_note_budget(
        archive_dir, subtitle_info, comment_info, evidence_count, article_info
    )
    archive_mod.write_readme(
        archive_dir, subtitle_info, article_info, comment_info, metadata_info, note_budget
    )

    print(
        json.dumps(
            {
                "archive_dir": str(archive_dir),
                "subtitles": subtitle_info,
                "evidence_blocks": evidence_count,
                "note_budget": note_budget,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
