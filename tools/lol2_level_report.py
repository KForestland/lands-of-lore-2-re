#!/usr/bin/env python3
"""Write one Markdown sheet per LoL2 level from the original level archives.

For each level archive DAT/L<n>_<xx>.MIX (and its companion L<n>_<xx>I.MIX) the
sheet lists, all read from the files:
  - the archive's entries and what each one is (level data entry, texture
    container, the entry holding the 147-byte entity records, other);
  - geometry and object counts from the level data entry header, and region/portal
    statistics from the region table;
  - the script streams: command and group counts, opcode use, predicates;
  - exits: every level-transition command (destination level and entry) and
    the objects whose events point straight at that command's group;
  - wall rows by class and by side type (wall side or portal side);
  - event records by kind, with the native matcher of each kind;
  - movie scenes the scripts play (opcode 21) by scene id and name;
  - held-item tests (event kind 4, mode 3) by item record number;
  - entity records by name tag;
  - the companion archive's entries by kind (AUD sound, VQA movie, other).
No game text, pictures or sound are written; only ids, counts and offsets.

  lol2_level_report.py --data DAT --out DIR             # all 15 levels + README.md
  lol2_level_report.py --data DAT --out DIR --level 9   # one level
  lol2_level_report.py --check --data DAT               # one line: every level reads cleanly, and docs/levels matches the tool
"""
from cli_errors import run_cli
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


ITEM_KEY = 0xED7EC08D  # GLOBAL.MIX entry with the 170 x 91-byte item definitions (docs/formats/items.md)


def item_identities(data_dir):
    """Map item identity (record +0x18) -> record number, from DAT/GLOBAL.MIX."""
    import struct
    b = (Path(data_dir) / "GLOBAL.MIX").read_bytes()
    r = [x for x in S.parse_mix(b) if x["key"] == ITEM_KEY][0]
    e = b[r["offset"]:r["offset"] + r["size"]]
    base, n = struct.unpack_from("<I", e, 4)[0], struct.unpack_from("<I", e, 0x34)[0]
    return {struct.unpack_from("<I", e, base + 91 * i + 0x18)[0]: i for i in range(n)}


def item_tests(scripts):
    """Event kind 4 with mode (+4) 3: the native matcher 0xADC76 dispatches modes 0-7 through the table at
    VA 0xADBAC; entry 3 (0xADC84) compares the held item's identity (+0x18) with u32 +6."""
    import struct
    out = defaultdict(list)
    for o in scripts["objects"]:
        for ev in o["events"]:
            if ev.get("kind") == 4:
                raw = bytes.fromhex(ev["raw_hex"])
                if len(raw) >= 10 and raw[4] == 3:
                    out[struct.unpack_from("<I", raw, 6)[0]].append((o["ref"], raw[5]))
    return out


def geometry_stats(raw):
    """Vertex/region counts and portal statistics from the level data entry (docs/formats/geometry.md)."""
    import struct
    nv, nr = struct.unpack_from("<I", raw, 0x50)[0], struct.unpack_from("<I", raw, 0x58)[0]
    ro = struct.unpack_from("<I", raw, 0x0C)[0]
    regs = [struct.unpack_from("<22H", raw, ro + 44 * i) for i in range(nr)]
    bad_v = sum(1 for r in regs for v in r[6:10] if v >= nv)
    links = [(i, s, r[2 + s]) for i, r in enumerate(regs) for s in range(4) if r[2 + s] != 0xFFFF]
    bad_n = sum(1 for _, _, n in links if n >= nr)
    recip = shared = 0
    for i, s, n in links:
        if n >= nr:
            continue
        recip += i in regs[n][2:6]
        edge = {regs[i][6 + s], regs[i][6 + (s + 1) % 4]}
        shared += any({regs[n][6 + t], regs[n][6 + (t + 1) % 4]} == edge for t in range(4))
    return dict(vertices=nv, regions=nr, links=len(links), reciprocal=recip, shared=shared, bad=bad_v + bad_n,
                walls=sum(1 for r in regs for s in range(4) if r[2 + s] == 0xFFFF),
                slope_floor=sum(1 for r in regs if r[14] & 4), slope_ceiling=sum(1 for r in regs if r[14] & 8))


def wall_stats(raw):
    """Wall table (header +0x08 offset, +0x54 count, 8-byte rows); region word 13 = first row, byte 30 = count
    (native 0xF4370-0xF438E). Code = row byte 5 & 0x1F: bits 0-1 side, bits 2-3 class, bit 4 special."""
    import struct
    u = lambda o: struct.unpack_from("<I", raw, o)[0]
    ws, wc, ro, nr = u(0x08), u(0x54), u(0x0C), u(0x58)
    regs = [struct.unpack_from("<22H", raw, ro + 44 * i) for i in range(nr)]
    owner, bad = {}, 0
    by = Counter()
    special_with_base = 0
    for i, r in enumerate(regs):
        n = r[15] & 0xFF
        if n == 0:
            bad += r[13] != 0xFFFF
            continue
        if r[13] + n > wc:
            bad += 1
            continue
        earlier_codes = set()
        for k in range(r[13], r[13] + n):
            bad += k in owner
            owner[k] = i
            code = raw[ws + 8 * k + 5] & 0x1F
            if code & 16:
                by["special"] += 1
                special_with_base += (code & 15) in earlier_codes
            else:
                by[("wall side" if r[2 + (code & 3)] == 0xFFFF else "portal side", code & 12)] += 1
            earlier_codes.add(code)
    bad += len(owner) != wc or ws + 8 * wc != ro
    return dict(rows=wc, regions_with_walls=sum(1 for r in regs if r[15] & 0xFF),
                by=by, special_with_base=special_with_base, bad=bad)


# Event record kinds and their native matchers (docs/lol2-script-events.md#event-records).
EVENT_KINDS = {
    ("object", 1): "14-byte record; native consumer open",
    ("object", 2): "periodic timer (0xB47B4 / 0xB8BA0)",
    ("object", 3): "event byte match (0xAD7F4)",
    ("object", 4): "held-item test (0xADD23, mode table VA 0xADBAC)",
    ("object", 5): "event and value match (0xAD8E0)",
    ("object", 6): "value match (0xADDE0)",
    ("object", 7): "health threshold (0xAE134)",
    ("object", 8): "word match with 0xFFFF wildcard (0xAE510)",
    ("object", 9): "hit filter (0xAE2C8)",
    ("object", 10): "region-or-object match (0xAE608)",
    ("object", 19): "predicate trailer (0x66AB0)",
    ("region", 11): "region selector and event (0xF2FC0)",
    ("region", 12): "region event (0xF2D87)",
    ("region", 15): "region comparison (0xF37C8)",
    ("region", 19): "predicate trailer (0x66AB0)",
}


def event_kinds(scripts):
    c = Counter()
    for o in scripts["objects"]:
        if o["table"] != "region":
            for ev in o["events"]:
                c[("object", ev["kind"])] += 1
    for rl in scripts["region_lists"]:
        for ev in rl["records"]:
            c[("region", ev["kind"])] += 1
    return c


def groups(raw):
    """Sizes of the portal-connected region groups, largest first."""
    import struct
    nr = struct.unpack_from("<I", raw, 0x58)[0]
    ro = struct.unpack_from("<I", raw, 0x0C)[0]
    parent = list(range(nr))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i in range(nr):
        for n in struct.unpack_from("<4H", raw, ro + 44 * i + 4):
            if n != 0xFFFF and n < nr:
                parent[find(i)] = find(n)
    return sorted(Counter(find(i) for i in range(nr)).values(), reverse=True)


def scene_names(data_dir):
    """The 86-name movie scene table in LOLG.DAT (file 0x1CF58C; name pointers are data addresses,
    file = data + 0x1C1024), limit dword at file 0x1CF764 (docs/lol2-movie-scenes.md)."""
    import struct
    exe = Path(data_dir).resolve().parent / "LOLG.DAT"
    if not exe.exists():
        return {}
    b = exe.read_bytes()
    limit = struct.unpack_from("<I", b, 0x1CF764)[0]
    out = {}
    for i in range(limit + 1):
        p = struct.unpack_from("<I", b, 0x1CF58C + 4 * i)[0] + 0x1C1024
        out[i] = b[p:b.index(b"\0", p)].decode("ascii", "replace")
    return out


def scenes_played(scripts):
    """Opcode 21 commands: byte 4 is the scene id (high dispatcher arm 0x6486A -> player 0xCF2B4)."""
    from collections import Counter
    c = Counter()
    for g in scripts["groups"]:
        for cmd in g["commands"]:
            if cmd["opcode"] == 21:
                c[bytes.fromhex(cmd["raw_hex"])[4]] += 1
    return c


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



def placed_item_groups(raw, scripts):
    """Check stream-1 references on the placed-item rows loaded by 0x94078."""
    import struct
    _, count, items = X.section(raw, 0x20, 0x6C, 37)
    _, _, events = X.section(raw, *X.OBJECT_EVENTS, 1)
    groups = {group["group"] for group in scripts["groups"] if group["stream"] == 1}
    indexed = {event["group"] for obj in scripts["objects"] if obj["table"] != "region"
               for event in obj["events"] if "group" in event}
    added = set()
    for index in range(count):
        start = struct.unpack_from("<H", items, index * 37 + 0x0C)[0]
        rows, _ = X.walk(events, start)
        for offset, record in rows:
            if record[1] not in X.OBJECT_GROUP_KINDS:
                continue
            target = struct.unpack_from("<H", record, 2)[0]
            if target not in groups:
                raise ValueError(f"placed item {index} event {offset:#x} names unknown group {target}")
            if target not in indexed:
                added.add(target)
    return count, added


def exit_predicates(scripts):
    """Join exit and other serialized event predicates to shared leaves."""
    predicates = [bytes.fromhex(row) for row in scripts["predicate_table"]["entries"]]

    def shared_slots(index, ancestors):
        if index in ancestors or index >= len(predicates):
            raise ValueError(f"invalid exit predicate reference {index}")
        row = predicates[index]
        slots = set()
        for kind, operand in (row[1:3], row[3:5]):
            if kind == 2:
                slots.add(operand)
            elif kind == 4:
                slots.update(shared_slots(operand, ancestors | {index}))
        return slots

    object_events = (event for obj in scripts["objects"] if obj["table"] != "region"
                     for event in obj["events"])
    region_events = (event for entry in scripts["region_lists"] for event in entry["records"])
    by_group = defaultdict(dict)
    for events in (object_events, region_events):
        for event in events:
            if "group" in event:
                key = (event["stream"], event["group"])
                by_group[key][event["file_offset"]] = event
    direct = guarded = 0
    shared = []
    exit_groups = set()
    for command in scripts["transitions"]:
        key = (command["stream"], command["group"])
        exit_groups.add(key)
        events = by_group[key]
        direct += bool(events)
        for event in events.values():
            predicate = event.get("predicate")
            if predicate is None:
                continue
            guarded += 1
            slots = shared_slots(predicate["index"], set())
            if slots:
                shared.append((command["file_offset"], event["file_offset"], sorted(slots)))
    other = []
    for key, events in by_group.items():
        if key in exit_groups:
            continue
        for event in events.values():
            predicate = event.get("predicate")
            if predicate is not None:
                slots = shared_slots(predicate["index"], set())
                if slots:
                    other.append((key, event["file_offset"], predicate["index"], tuple(sorted(slots))))
    return direct, guarded, shared, other


def check_render_routes(image):
    for address, sequence in (
        (0x129C23, "e88c7d0000c1f80883c40c2500ff000089842488000000"),
        (0x12AA4B, "8b512883fa000f8421ffffff"),
        (0x12AA90, "8a5c05008a540d00"),
        (0x13227F, "8a442424884424578a442428884424568a44242c884424558b442454"),
        (0x125FD3, "f6c4107406b858d00c00c3f6c4017406b890d10c00c3a8207406b8c4d10c00c3"),
        (0x126200, "a1a0d80f0031d2668b500289118b5424040faf1183c00801d0c3"),
        (0x114753, "e84cdb010083c4148b0424d1f883c74666894632"),
        (0x114951, "0314246bd20ca1782d020001c2"),
        (0x12759E, "8a4130c1e010898424fc03000031c08a4131c1e010"),
    ):
        expected = bytes.fromhex(sequence)
        start = address + 0x37000
        if image[start:start + len(expected)] != expected:
            raise ValueError(f"render route at {address:#x}")


def check_l8_controls(data_dir):
    """Join the original control and prop placements to their region rows."""
    from struct import unpack_from

    source = (Path(data_dir) / "L8_SJ.MIX").read_bytes()
    entry, geometry = S.level_geometry(source)
    vertices, _, regions = unpack_from("<3I", geometry, 4)
    props, controls = unpack_from("<2I", geometry, 0x14)
    expected = ((controls + 69 * 33, 678, 0xCE8868),
                (controls + 114 * 33, 3206, 0xCE8E35),
                (controls + 116 * 33, 3300, 0xCE8E77),
                (props + 115 * 37, 3747, 0xCD9B27),
                (props + 1014 * 37, 3209, 0xCE1D16))
    for row, region, absolute in expected:
        if entry["offset"] + row != absolute or unpack_from("<h", geometry, row + 10)[0] != region:
            raise ValueError("L8 control or linked prop region")
    lower, upper = (regions + 44 * index for index in (678, 657))
    if (unpack_from("<h", geometry, lower + 0x14)[0] != -10
            or unpack_from("<h", geometry, upper + 0x14)[0] != 100):
        raise ValueError("L8 control 69 floor heights")
    x, y, z = unpack_from("<hhh", source, 0xCD476E + 4)
    corners = unpack_from("<4H", geometry, upper + 0xC)
    polygon = [unpack_from("<ii", geometry, vertices + 8 * corner) for corner in corners]
    cross = [(bx - ax) * ((y << 16) - ay) - (by - ay) * ((x << 16) - ax)
             for (ax, ay), (bx, by) in zip(polygon, polygon[1:] + polygon[:1])]
    if z != 100 or min(cross) < 0 < max(cross):
        raise ValueError("L8 control 69 sequence destination")
    left, right = (regions + 44 * index for index in (3206, 3209))
    if (unpack_from("<H", geometry, left + 8)[0] != 3209
            or unpack_from("<H", geometry, right + 4)[0] != 3206
            or unpack_from("<HH", geometry, left + 16) != (833, 909)
            or unpack_from("<HH", geometry, right + 12) != (909, 833)):
        raise ValueError("L8 control 114 reciprocal edge")


def read_level(data_dir, stem):
    path = Path(data_dir) / f"{stem}.MIX"
    b = path.read_bytes()
    rows = S.parse_mix(b)
    geo, geo_raw = S.level_geometry(b)
    tex = {}
    for n, key in texture_key(stem):
        for r in rows:
            if r["key"] == key:
                tex[r["index"]] = n
    odf, start, count = E.locate_entity_table(b, stem)
    records = E.extract_entities(b, start, count)
    ent_entry = (odf["index"], start - odf["offset"], start)
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
    gs = geometry_stats(geo_raw)
    gs["groups"] = groups(geo_raw)
    gs["wall_rows"] = wall_stats(geo_raw)
    gs["placed_item_groups"] = placed_item_groups(geo_raw, scripts)
    return dict(stem=stem, size=len(b), rows=rows, geo=geo, geom=gs, tex=tex, ent_entry=ent_entry, records=records,
                scripts=scripts, comp=comp)


def sheet(L, names, items, scenes):
    s, sc, c = L["stem"], L["scripts"], L["scripts"]["counts"]
    t = c["object_tables"]
    raw_geo = None
    lines = [f"# {s}", "",
             f"Made by `tools/lol2_level_report.py` from `DAT/{s}.MIX`"
             + (f" and `DAT/{L['comp'][0]}`" if L["comp"] else "")
             + ". Formats: [MIX](../formats/mix.md), [level data](../formats/level-data.md), "
               "[texture container](../formats/texture-container.md), [entity records](../formats/entity-records.md). "
               "How to read it: [README](README.md).", "",
             f"Related references: [Progression rows for {s}](../PROGRESSION.md#level-{s.lower()}) and [item, spell and creature numbers](../NUMBERS.md).", "",
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
    G = L["geom"]
    lines += ["## Regions and portals", "",
              "From the vertex and region tables ([geometry](../formats/geometry.md)). A link is a region side whose "
              "neighbour word names another region (a portal); a side without one is a wall.", "",
              "| Vertices | Regions | Portal links | Reciprocal | Sharing the side's two vertices | Wall sides | Sloped floors | Sloped ceilings |",
              "|---:|---:|---:|---:|---:|---:|---:|---:|",
              f"| {G['vertices']:,} | {G['regions']:,} | {G['links']:,} | {G['reciprocal']:,} | {G['shared']:,} | "
              f"{G['walls']:,} | {G['slope_floor']:,} | {G['slope_ceiling']:,} |", "",
              f"Following the portal links, the regions fall into {len(G['groups'])} connected groups: "
              + ", ".join(f"{n:,}" for n in G["groups"][:8]) + (" …" if len(G["groups"]) > 8 else "")
              + " regions ([maps](../formats/maps.md)).", ""]
    W = G["wall_rows"]
    lines += ["## Walls", "",
              f"{W['rows']:,} wall rows of 8 bytes, owned by {W['regions_with_walls']:,} regions, each row by exactly one region "
              "([walls](../formats/walls.md)). Class = bits 2-3 of the row's code; the side is bits 0-1.", "",
              "| Side | Class 0 | Class 4 | Class 8 | Class 12 |", "|---|---:|---:|---:|---:|"]
    for side in ("wall side", "portal side"):
        lines.append(f"| {side} | " + " | ".join(f"{W['by'].get((side, c), 0):,}" for c in (0, 4, 8, 12)) + " |")
    lines += ["", f"Special rows (code bit 4): {W['by'].get('special', 0):,}.", ""]
    lines += ["## Scripts", "",
              "| Stream | Commands | Groups | Bytes |", "|---:|---:|---:|---:|"]
    for st in sc["streams"]:
        lines.append(f"| {st['stream']} | {st['command_count']:,} | {st['group_count']:,} | {st['size']:,} |")
    use = sorted(((int(k), v) for k, v in c["opcode_use"].items()), key=lambda kv: (-kv[1], kv[0]))
    lines += ["", f"{c['commands']:,} commands in {c['groups']:,} groups use {c['distinct_opcodes']} distinct opcodes "
              f"(meanings: [script format](../lol2-level-script-format.md)). Predicate table: {c['predicate_entries']} "
              f"entries of 5 bytes. Commands outside the opcode size table: {len(sc['unsupported'])}.", "",
              "Opcode use: " + ", ".join(f"{k} ×{v}" for k, v in use) + ".", ""]
    ek = event_kinds(sc)
    lines += ["Event records by kind ([native matchers](../lol2-script-events.md#event-records)):", "",
              "| List | Kind | Records | What the game does with it |", "|---|---:|---:|---|"]
    for (lst, k), n in sorted(ek.items()):
        lines.append(f"| {lst} | {k} | {n:,} | {EVENT_KINDS.get((lst, k), 'not in the events page')} |")
    lines.append("")
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
    played = scenes_played(sc)
    lines += ["", "## Movie scenes", ""]
    if played:
        lines += ["Opcode 21 commands name a scene id from the executable's 86-name table "
                  "([movie scenes](../lol2-movie-scenes.md)); the movie file is `<name>.vqa`.", "",
                  "| Scene id | Name | Commands |", "|---:|---|---:|"]
        for sid, n in sorted(played.items()):
            lines.append(f"| {sid} | `{scenes.get(sid, '?')}` | {n} |")
    else:
        lines.append("No opcode-21 command in this level's scripts.")
    tests = item_tests(sc)
    lines += ["", "## Held-item tests", ""]
    if tests:
        lines += ["Event records of kind 4 with mode 3: the object's event runs when the held item has this identity "
                  "([events](../lol2-script-events.md#event-records); mode table at VA `0xADBAC`, compare at `0xADC84`). "
                  "Item = record number in the [item table](../formats/items.md). Byte +5 nonzero inverts the test.", "",
                  "| Item | Identity | Objects (inverted marked !) |", "|---:|---|---|"]
        for ident, refs in sorted(tests.items(), key=lambda kv: items.get(kv[0], 999)):
            who = ", ".join(("!" if inv else "") + ref for ref, inv in refs[:8]) + (" …" if len(refs) > 8 else "")
            lines.append(f"| {items.get(ident, '?')} | 0x{ident:08X} | {who} |")
    else:
        lines.append("None in this level.")
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
             "| Level | Entries | Actors | Props | Controls | Movables | Commands | Item tests | Exits to |", "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for L in levels:
        c = L["scripts"]["counts"]; t = c["object_tables"]
        dests = sorted({x["destination_level"] for x in L["scripts"]["transitions"]})
        lines.append(f"| [{L['stem']}]({L['stem']}.md) | {len(L['rows'])} | {t.get('actor', 0)} | {t.get('prop', 0)} | "
                     f"{t.get('control', 0)} | {t.get('movable', 0)} | {c['commands']:,} | "
                     f"{sum(len(v) for v in item_tests(L['scripts']).values())} | "
                     f"{', '.join('L' + str(d) for d in dests) or '—'} |")
    lines += ["", "Sections of a sheet:", "",
              "- **Archive entries**: every MIX entry with its key, file offset and size, and what it is when known: "
              "the level data entry (found by its header), the texture container (found by the hash of its name) and "
              "the entry that holds the 147-byte entity records.",
              "- **Geometry and objects**: table counts from the level data header.",
              "- **Scripts**: the two command streams framed with the native size table; how often each opcode occurs.",
              "- **Exits**: the level-transition commands and the objects whose events name their group.",
              "- **Held-item tests**: event records that run when the held item has a given identity (kind 4, mode 3), "
              "by item record number.",
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
        exit_checks = [exit_predicates(L["scripts"]) for L in levels]
        direct_exits = sum(direct for direct, _, _, _ in exit_checks)
        guarded_exits = sum(guarded for _, guarded, _, _ in exit_checks)
        shared_exits = [row for _, _, rows, _ in exit_checks for row in rows]
        nonexit_shared = [row for _, _, _, rows in exit_checks for row in rows]
        nonexit_group_count = sum(len({key for key, *_ in rows}) for _, _, _, rows in exit_checks)
        nonexit_slots = {slot for _, _, _, slots in nonexit_shared for slot in slots}
        try:
            check_render_routes((Path(a.data).resolve().parent / "LOLG.DAT").read_bytes())
        except (OSError, ValueError) as error:
            bad.append(str(error))
        expected_shared = [(0x5E93F4, 0x5EC32A, [52]), (0x5E93FA, 0x5EC336, [52])]
        if len(stems) == 15 and (direct_exits, guarded_exits, shared_exits) != (72, 24, expected_shared):
            bad.append("exit predicate census changed")
        expected_nonexit = {
            ((0, 432), 0x6FDB2F, 51, (45,)), ((1, 13416), 0xCD7FDA, 108, (12, 13, 46)),
            ((1, 5510), 0x95FC40, 7, (12,)), ((1, 6886), 0xECE1E3, 1, (0,)),
        }
        if len(stems) == 15 and (
            (len(nonexit_shared), nonexit_group_count, len(nonexit_slots)) != (289, 287, 28)
            or not expected_nonexit.issubset(nonexit_shared)
        ):
            bad.append("non-exit shared predicate census changed")
        tex = sum(1 for L in levels if L["tex"])
        ent = sum(1 for L in levels if L["records"])
        uns = sum(len(L["scripts"]["unsupported"]) for L in levels)
        items = item_identities(a.data)
        tests = [k for L in levels for k, v in item_tests(L["scripts"]).items() for _ in v]
        unknown = sum(1 for k in tests if k not in items)
        sn = scene_names(a.data)
        sp = Counter()
        for L in levels:
            sp.update(scenes_played(L["scripts"]))
        bad_scene = sorted(k for k in sp if sn and k not in sn)
        gl = sum(L["geom"]["links"] for L in levels); gr = sum(L["geom"]["reciprocal"] for L in levels)
        gs = sum(L["geom"]["shared"] for L in levels); gb = sum(L["geom"]["bad"] for L in levels)
        wb = sum(L["geom"]["wall_rows"]["bad"] for L in levels); wr = sum(L["geom"]["wall_rows"]["rows"] for L in levels)
        special = sum(L["geom"]["wall_rows"]["by"]["special"] for L in levels)
        based = sum(L["geom"]["wall_rows"]["special_with_base"] for L in levels)
        if len(stems) == 15 and (special, based) != (67, 45):
            bad.append(f"special wall counts {(special, based)}")
        item_rows = sum(L["geom"]["placed_item_groups"][0] for L in levels)
        item_groups = sum(len(L["geom"]["placed_item_groups"][1]) for L in levels)
        if len(stems) == 15 and (item_rows, item_groups) != (663, 57):
            bad.append(f"placed-item row/group counts {(item_rows, item_groups)}")
        l1 = next((L for L in levels if L["stem"] == "L1_DC"), None)
        if l1 and 13584 not in l1["geom"]["placed_item_groups"][1]:
            bad.append("placed-item group 13584 missing from L1_DC")
        if "L8_SJ" in stems:
            try:
                check_l8_controls(a.data)
            except (OSError, ValueError) as error:
                bad.append(str(error))
        ev = Counter()
        for L in levels:
            ev.update(event_kinds(L["scripts"]))
        unknown_kinds = sorted(k for k in ev if k not in EVENT_KINDS)
        differ = []
        if len(stems) == len(level_files(a.data)):
            root = Path(__file__).resolve().parents[1] / "docs" / "levels"
            for L in levels:
                path = root / f"{L['stem']}.md"
                if not path.is_file() or path.read_text(encoding="utf-8") != sheet(L, names, items, sn):
                    differ.append(L["stem"])
            readme_path = root / "README.md"
            if not readme_path.is_file() or readme_path.read_text(encoding="utf-8") != readme(levels):
                differ.append("README")
            if differ:
                bad.append("sheets differ: " + ", ".join(differ))
        sheet_note = "sheets match docs/levels" if not differ else "sheets differ"
        print(f"CHECK level_report: {len(levels)}/{len(stems)} level archives read (level data entry, scripts framed, "
              f"{uns} commands outside the size table); texture container found by name hash in {tex}; entity records in "
              f"{ent}; {exits} level-transition commands ({direct_exits} directly linked, {guarded_exits} predicate links, "
              f"{len(shared_exits)} with shared bytes); {len(nonexit_shared)} other shared predicate records; "
              f"regions {sum(L['geom']['regions'] for L in levels):,}, "
              f"out-of-range vertex/neighbour indices {gb}, portal links {gl:,} (reciprocal {gr:,}, sharing the side's vertices "
              f"{gs:,}); wall rows {wr:,}, partition faults {wb}, {special} special ({based} with earlier base); event records {sum(ev.values()):,} (kinds without a documented matcher: {unknown_kinds or 'none'}); "
              f"opcode-21 movie commands {sum(sp.values())} naming {len(sp)} scene ids (outside the scene table: {bad_scene or 'none'}); held-item tests (kind 4 mode 3) {len(tests)}, identity not in the item table: "
              f"{unknown}; {item_rows} placed-item rows name {item_groups} additional groups; {sheet_note}; bad={bad or 'none'}")
        return 0 if not bad and not uns and not unknown and not gb and not wb and not bad_scene else 1
    items = item_identities(a.data)
    scenes = scene_names(a.data)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for L in levels:
        (out / f"{L['stem']}.md").write_text(sheet(L, names, items, scenes), encoding="utf-8")
    if a.level is None:
        (out / "README.md").write_text(readme(levels), encoding="utf-8")
    print(f"wrote {len(levels)} sheets to {out}" + (f"; failed: {bad}" if bad else ""))
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
