#!/usr/bin/env python3
"""Write one Markdown sheet per LoL2 level from the original level archives.

For each level archive DAT/L<n>_<xx>.MIX (and its companion L<n>_<xx>I.MIX) the
sheet lists, all read from the files:
  - the archive's entries and what each one is (level data entry, texture
    container, the entry holding the 147-byte entity records, other);
  - geometry and object counts from the level data entry header;
  - the script streams: command and group counts, opcode use, predicates;
  - exits: every level-transition command (destination level and entry) and
    the objects whose events point straight at that command's group;
  - entity records by name tag;
  - the companion archive's entries by kind (AUD sound, VQA movie, other).
No game text, pictures or sound are written; only ids, counts and offsets.

  lol2_level_report.py --data DAT --out DIR             # all 15 levels + README.md
  lol2_level_report.py --data DAT --out DIR --level 9   # one level
  lol2_level_report.py --check --data DAT               # one line: every level reads cleanly
"""
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lol2_cli  # noqa: E402
import lol2_source_format as S  # noqa: E402
import lol2_export_scripts as X  # noqa: E402
import lol2_entity_field_analyzer as E  # noqa: E402
from lol2_westwood_hash import ww_hash_v1  # noqa: E402
from lol2_aud_decode import is_aud  # noqa: E402


def level_files(data_dir):
    out = []
    for f in lol2_cli.mix_files(data_dir):
        stem = f[:-4].upper()
        if stem.startswith("L") and "_" in stem and not stem.endswith("I") and stem.split("_")[0][1:].isdigit():
            out.append(stem)
    return sorted(out, key=lambda s: int(s.split("_")[0][1:]))


def texture_key(stem):
    for n in range(1, 10):
        key = ww_hash_v1(f"SPHERE{n}\\{stem}\\{stem}.TE_")
        yield n, key


def read_level(data_dir, stem):
    path = Path(data_dir) / f"{stem}.MIX"
    b = path.read_bytes()
    rows = S.parse_mix(b)
    geo, _ = S.level_geometry(b)
    tex = {}
    for n, key in texture_key(stem):
        for r in rows:
            if r["key"] == key:
                tex[r["index"]] = n
    ent = E.find_entity_region(b)
    records, ent_entry = [], None
    if ent:
        base, first, last = ent
        records = E.extract_entities(b, base, first, last)
        start = base + first * E.RECORD_SIZE
        for r in rows:
            if r["offset"] <= start < r["offset"] + r["size"]:
                ent_entry = (r["index"], start - r["offset"], start)
    scripts = X.export(path)
    companion = Path(data_dir) / f"{stem}I.MIX"
    comp = None
    if companion.exists():
        cb = companion.read_bytes()
        kinds = Counter()
        for r in S.parse_mix(cb):
            e = cb[r["offset"]:r["offset"] + r["size"]]
            kinds["AUD sound" if is_aud(e) else "VQA movie" if e[:4] == b"FORM" and e[8:12] == b"WVQA" else "other"] += 1
        comp = (companion.name, len(cb), kinds)
    return dict(stem=stem, size=len(b), rows=rows, geo=geo, tex=tex, ent_entry=ent_entry, records=records,
                scripts=scripts, comp=comp)


def sheet(L, names):
    s, sc, c = L["stem"], L["scripts"], L["scripts"]["counts"]
    t = c["object_tables"]
    raw_geo = None
    lines = [f"# {s}", "",
             f"Made by `tools/lol2_level_report.py` from `DAT/{s}.MIX`"
             + (f" and `DAT/{L['comp'][0]}`" if L["comp"] else "")
             + ". Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), "
               "[texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). "
               "How to read it: [README](README.md).", "",
             "## Archive entries", "",
             f"`{s}.MIX` is {L['size']:,} bytes with {len(L['rows'])} entries.", "",
             "| Entry | Key | File offset | Size | What it is |", "|---:|---|---:|---:|---|"]
    for r in L["rows"]:
        what = []
        if r["index"] == L["geo"]["index"]:
            what.append("level data (header dword 0 = 18, dword 4 = 5300)")
        if r["index"] in L["tex"]:
            n = L["tex"][r["index"]]
            what.append(f"texture container: key = `ww_hash_v1(\"SPHERE{n}\\{s}\\{s}.TE_\")`")
        if L["ent_entry"] and r["index"] == L["ent_entry"][0]:
            what.append(f"holds the entity records from entry byte {L['ent_entry'][1]:,}")
        lines.append(f"| {r['index']} | 0x{r['key']:08X} | {r['offset']:,} | {r['size']:,} | {'; '.join(what) or 'not identified'} |")
    lines += ["", "## Geometry and objects", "",
              "Counts from the level data entry header ([field table](../formats/level-data.md#header-tables)).", "",
              "| Table | Count |", "|---|---:|"]
    for k in ("actor", "prop", "control", "movable"):
        lines.append(f"| {k}s | {t.get(k, 0):,} |")
    lines += [f"| region descriptors | {c['region_descriptors']:,} |",
              f"| objects with an event list | {c['objects']:,} |", ""]
    lines += ["## Scripts", "",
              "| Stream | Commands | Groups | Bytes |", "|---:|---:|---:|---:|"]
    for st in sc["streams"]:
        lines.append(f"| {st['stream']} | {st['command_count']:,} | {st['group_count']:,} | {st['size']:,} |")
    use = sorted(((int(k), v) for k, v in c["opcode_use"].items()), key=lambda kv: (-kv[1], kv[0]))
    lines += ["", f"{c['commands']:,} commands in {c['groups']:,} groups use {c['distinct_opcodes']} distinct opcodes "
              f"(meanings: [script format](../lol2-level-script-format.md)). Predicate table: {c['predicate_entries']} "
              f"entries of 5 bytes. Commands outside the opcode size table: {len(sc['unsupported'])}.", "",
              "Opcode use: " + ", ".join(f"{k} ×{v}" for k, v in use) + ".", ""]
    links = defaultdict(list)
    for o in sc["objects"]:
        for ev in o["events"]:
            if ev.get("stream") is not None and ev.get("group") is not None:
                links[(ev["stream"], ev["group"])].append(o["ref"])
    lines += ["## Exits", ""]
    if sc["transitions"]:
        lines += ["Level-transition commands (bytes `02 01 00 00 1c`, then level in the low 5 bits and entry in the "
                  "high 3 bits of byte 5). \"Started by\" lists the objects whose event list names the command's "
                  "group directly; a dash means the group is reached another way (not traced here).", "",
                  "| To level | Entry | Stream | Group | Started by |", "|---|---:|---:|---:|---|"]
        for tr in sorted(sc["transitions"], key=lambda x: (x["destination_level"], x["destination_entry"], x["group"])):
            dest = names.get(tr["destination_level"], f"L{tr['destination_level']} (no archive)")
            who = links.get((tr["stream"], tr["group"]), [])
            lines.append(f"| {dest} | {tr['destination_entry']} | {tr['stream']} | {tr['group']} | "
                         f"{', '.join(who[:6]) + (' …' if len(who) > 6 else '') if who else '—'} |")
    else:
        lines.append("No level-transition command in this archive's scripts.")
    lines += ["", "## Entity records", ""]
    if L["records"]:
        tags = Counter(r["tag"] for r in L["records"])
        lines.append(f"{len(L['records'])} records of 147 bytes, by name tag: "
                     + ", ".join(f"`{k}` ×{v}" for k, v in sorted(tags.items(), key=lambda kv: (-kv[1], kv[0]))) + ".")
    else:
        lines.append("No 147-byte entity records found by name tag.")
    lines += ["", "## Companion archive", ""]
    if L["comp"]:
        name, size, kinds = L["comp"]
        lines.append(f"`{name}`, {size:,} bytes: " + ", ".join(f"{v} {k}" for k, v in sorted(kinds.items())) + ".")
    else:
        lines.append("None.")
    lines += ["", "## Open", "",
              "- Which entries marked \"not identified\" hold what ([Q19](../OPEN_QUESTIONS.md) for the entity records).",
              "- Opcode meanings and record kinds ([Q4](../OPEN_QUESTIONS.md), [Q5](../OPEN_QUESTIONS.md)); per-level puzzle logic "
              "([Q18](../OPEN_QUESTIONS.md)).", ""]
    return "\n".join(lines)


def readme(levels):
    lines = ["# Level sheets", "",
             "One sheet per level archive, written by `tools/lol2_level_report.py --data DAT --out docs/levels` from the "
             "original files only: entry roles, object counts, script statistics, exits and entity records. Ids and "
             "counts only; no game text. Every number on a sheet is regenerated by the tool.", "",
             "| Level | Entries | Actors | Props | Controls | Movables | Commands | Exits to |", "|---|---:|---:|---:|---:|---:|---:|---|"]
    for L in levels:
        c = L["scripts"]["counts"]; t = c["object_tables"]
        dests = sorted({x["destination_level"] for x in L["scripts"]["transitions"]})
        lines.append(f"| [{L['stem']}]({L['stem']}.md) | {len(L['rows'])} | {t.get('actor', 0)} | {t.get('prop', 0)} | "
                     f"{t.get('control', 0)} | {t.get('movable', 0)} | {c['commands']:,} | "
                     f"{', '.join('L' + str(d) for d in dests) or '—'} |")
    lines += ["", "Sections of a sheet:", "",
              "- **Archive entries**: every MIX entry with its key, file offset and size, and what it is when known: "
              "the level data entry (found by its header), the texture container (found by the hash of its name) and "
              "the entry that holds the 147-byte entity records.",
              "- **Geometry and objects**: table counts from the level data header.",
              "- **Scripts**: the two command streams framed with the native size table; how often each opcode occurs.",
              "- **Exits**: the level-transition commands and the objects whose events name their group.",
              "- **Entity records** and the **companion archive** `L<n>_<xx>I.MIX` (sounds and movies).", ""]
    return "\n".join(lines)


def main():
    ap = lol2_cli.tool_args((__doc__ or ""))
    ap.add_argument("--level", type=int)
    a = ap.parse_args()
    stems = level_files(a.data)
    if a.level is not None:
        stems = [s for s in stems if int(s.split("_")[0][1:]) == a.level]
    names = {int(s.split("_")[0][1:]): s for s in level_files(a.data)}
    if not a.check and not a.out:
        ap.print_help(); return 2
    levels, bad = [], []
    for s in stems:
        try:
            levels.append(read_level(a.data, s))
        except Exception as ex:  # report every level, stop at the end
            bad.append(f"{s}: {ex}")
    if a.check:
        exits = sum(len(L["scripts"]["transitions"]) for L in levels)
        tex = sum(1 for L in levels if L["tex"])
        ent = sum(1 for L in levels if L["records"])
        uns = sum(len(L["scripts"]["unsupported"]) for L in levels)
        print(f"CHECK level_report: {len(levels)}/{len(stems)} level archives read (level data entry, scripts framed, "
              f"{uns} commands outside the size table); texture container found by name hash in {tex}; entity records in "
              f"{ent}; {exits} level-transition commands; bad={bad or 'none'}")
        return 0 if not bad and not uns else 1
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for L in levels:
        (out / f"{L['stem']}.md").write_text(sheet(L, names), encoding="utf-8")
    if a.level is None:
        (out / "README.md").write_text(readme(levels), encoding="utf-8")
    print(f"wrote {len(levels)} sheets to {out}" + (f"; failed: {bad}" if bad else ""))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
