#!/usr/bin/env python3
"""Plot an original LoL2 level's regions, wall sides, portals and placements.

  lol2_level_schematic.py --data DAT --level 1 --out /tmp/l1.png
  lol2_level_schematic.py --data DAT --level 1 --focus 1029 --radius 450 --out /tmp/door.png
  lol2_level_schematic.py --data DAT --check

The PNG is a schematic. It uses original geometry and placement records,
with labels drawn by Pillow. Use --focus to inspect a dense area.
"""
from cli_errors import run_cli
from dataclasses import dataclass
from pathlib import Path
from struct import iter_unpack

import lol2_cli
from lol2_export_scripts import section
from lol2_level_map import s16
from lol2_level_report import level_files
from lol2_source_format import level_geometry

BACKGROUND = "#101b28"
INK = "#f4f1e8"
MUTED = "#a2b2c2"
FLOORS = ("#293d52", "#324a61", "#3b566d", "#476176", "#516a7c")
WALL = "#b7c7d3"
PORTAL = "#637b91"
DOOR = "#f8b65c"
ITEM = "#86e7cc"
CREATURE = "#f7a5b4"
FOCUS = "#6de1ff"


@dataclass(frozen=True)
class Placement:
    kind: str
    index: int
    x: int
    y: int
    region: int


def parse_geometry(raw):
    # Geometry header and placement widths are in docs/formats/level-data.md.
    _, _, vertices = section(raw, 4, 0x50, 8)
    _, _, regions = section(raw, 0x0C, 0x58, 44)
    verts = list(iter_unpack("<ii", vertices))
    regs = list(iter_unpack("<22H", regions))
    if not verts or not regs:
        raise ValueError("level has no vertices or regions")
    for index, row in enumerate(regs):
        if len(set(row[6:10])) != 4 or any(v >= len(verts) for v in row[6:10]):
            raise ValueError(f"region {index} has invalid corners")
        if any(n != 0xFFFF and n >= len(regs) for n in row[2:6]):
            raise ValueError(f"region {index} has an invalid neighbour")
    marks = []
    # 0xAE99A–0xAE9CB / 0xAEA30–0xAEA5C bind placement +0/+2 and +0x0A.
    for kind, offset, count, width in (("I", 0x20, 0x6C, 37), ("A", 0x1C, 0x68, 56)):
        _, _, rows = section(raw, offset, count, width)
        for at in range(0, len(rows), width):
            x = int.from_bytes(rows[at:at+2], "little", signed=True) << 16
            y = int.from_bytes(rows[at+2:at+4], "little", signed=True) << 16
            region = int.from_bytes(rows[at+10:at+12], "little", signed=True)
            if region != -1 and not 0 <= region < len(regs):
                raise ValueError(f"placement {kind}{at // width} has an invalid region")
            marks.append(Placement(kind, at // width, x, y, region))
    return verts, regs, marks


def edge_type(row, neighbour):
    """Identify a boundary, portal, or joined flat side with a collapsed region."""
    if neighbour is None:
        return "wall"
    if (not (row[14] | neighbour[14]) & 0x0C
            and (row[10] == row[11] or neighbour[10] == neighbour[11])):
        return "door"
    return "portal"


def bounds(verts, regs, focus, radius):
    if focus is None:
        xs, ys = zip(*verts)
        return min(xs), min(ys), max(xs), max(ys)
    if not 0 <= focus < len(regs):
        raise ValueError(f"no region {focus}")
    xs, ys = zip(*(verts[i] for i in regs[focus][6:10]))
    x, y = (min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2
    radius <<= 16
    return x - radius, y - radius, x + radius, y + radius


def overlapped(rect, others):
    x0, y0, x1, y1 = rect
    return any(x0 < r and x1 > l and y0 < b and y1 > t for l, t, r, b in others)


def draw(stem, verts, regs, placements, focus, radius, size):
    from PIL import Image, ImageDraw, ImageFont

    x0, y0, x1, y1 = bounds(verts, regs, focus, radius)
    scale = (size - 40) / max(x1 - x0, y1 - y0, 1)
    width = max(540, int((x1 - x0) * scale) + 40)
    height = max(200, int((y1 - y0) * scale) + 40)
    xpad = (width - (x1 - x0) * scale) / 2
    ypad = (height - (y1 - y0) * scale) / 2

    def point(x, y):
        return round(xpad + (x - x0) * scale), round(ypad + (y1 - y) * scale)

    floor, roof = min(s16(row[10]) for row in regs), max(s16(row[10]) for row in regs)
    canvas = Image.new("RGB", (width, height), BACKGROUND)
    plot = ImageDraw.Draw(canvas)
    edges = {"wall": set(), "portal": set(), "door": set()}
    for index, row in sorted(enumerate(regs), key=lambda pair: s16(pair[1][10])):
        polygon = [verts[v] for v in row[6:10]]
        xs, ys = zip(*polygon)
        if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1:
            continue
        shade = (len(FLOORS)-1) * (s16(row[10]) - floor) // max(1, roof - floor)
        corners = [point(*v) for v in polygon]
        plot.polygon(corners, fill=FLOORS[shade])
        for side, other in enumerate(row[2:6]):
            key = edge_type(row, regs[other] if other != 0xFFFF else None)
            segment = tuple(sorted((corners[side], corners[(side+1) % 4])))
            edges[key].add(segment)
    for name, color, stroke in (("portal", PORTAL, 1), ("wall", WALL, 2), ("door", DOOR, 4)):
        for segment in sorted(edges[name]):
            plot.line(segment, fill=color, width=stroke)
    if focus is not None:
        outline = [point(*verts[v]) for v in regs[focus][6:10]]
        plot.line([*outline, outline[0]], fill=BACKGROUND, width=5)
        plot.line([*outline, outline[0]], fill=FOCUS, width=2)

    mark_font = ImageFont.load_default(size=15)
    visible = [(mark, point(mark.x, mark.y)) for mark in placements
               if x0 <= mark.x <= x1 and y0 <= mark.y <= y1]
    reserved = [(px-6, py-6, px+7, py+7) for _, (px, py) in visible]
    hidden = 0
    for mark, (px, py) in visible:
        color = ITEM if mark.kind == "I" else CREATURE
        if mark.kind == "I":
            plot.ellipse((px-4, py-4, px+4, py+4), fill=color, outline=BACKGROUND)
        else:
            plot.polygon([(px, py-6), (px+6, py), (px, py+6), (px-6, py)], fill=color, outline=BACKGROUND)
        label = f"{mark.kind}{mark.index}"
        text_width = int(plot.textlength(label, font=mark_font)) + 8
        for dx, dy in ((9, -12), (-text_width-9, -12), (5, 11), (-text_width-5, 11),
                       (12, -30), (-text_width-12, -30), (8, 27), (-text_width-8, 27)):
            x, y = px + dx, py + dy
            box = (x, y, x+text_width, y+22)
            if x < 0 or y < 0 or box[2] >= width or box[3] >= height or overlapped(box, reserved):
                continue
            plot.line((px, py, max(x, min(px, box[2])), max(y, min(py, box[3]))), fill=color, width=1)
            plot.rectangle(box, fill=BACKGROUND)
            plot.text((x+4, y+2), label, fill=color, font=mark_font)
            reserved.append(box)
            break
        else:
            hidden += 1

    image = Image.new("RGB", (width, height + 172), BACKGROUND)
    image.paste(canvas, (0, 67))
    page = ImageDraw.Draw(image)
    title_font = ImageFont.load_default(size=27)
    caption_font = ImageFont.load_default(size=15)
    page.text((20, 13), f"{stem} / Level schematic", fill=INK, font=title_font)
    subtitle = "Full level" if focus is None else f"Region {focus} and adjacent geometry"
    page.text((21, 46), f"{subtitle}  |  +Y up  |  {len(visible)} placements in view", fill=MUTED, font=caption_font)
    page.line((20, 65, width-20, 65), fill=PORTAL)
    footer = height + 77
    page.line((20, footer-3, width-20, footer-3), fill=PORTAL)
    for x, color, caption in ((20, WALL, "Wall"), (105, PORTAL, "Portal"), (198, DOOR, "Collapsed portal / doorway candidate")):
        page.line((x, footer+13, x+20, footer+13), fill=color, width=3)
        page.text((x+27, footer+3), caption, fill=INK, font=caption_font)
    page.ellipse((21, footer+32, 31, footer+42), fill=ITEM)
    page.text((38, footer+27), "I  Placed item", fill=INK, font=caption_font)
    page.polygon([(161, footer+31), (167, footer+37), (161, footer+43), (155, footer+37)], fill=CREATURE)
    page.text((173, footer+27), "A  Actor (creature) placement", fill=INK, font=caption_font)
    if focus is not None:
        page.rectangle((374, footer+32, 389, footer+42), outline=FOCUS, width=2)
        page.text((396, footer+27), "Selected region", fill=INK, font=caption_font)
    page.text((20, footer+50), "Lighter floors are higher. Storeys can overlap.", fill=MUTED, font=caption_font)
    hint = (f"{hidden} crowded labels omitted. Use --focus and --radius to zoom."
            if hidden else "IDs are zero-based rows in the original placement tables.")
    page.text((20, footer+73), hint, fill=MUTED, font=caption_font)
    return image, len(visible), hidden


def load(data, stem):
    _, raw = level_geometry((data / f"{stem}.MIX").read_bytes())
    return parse_geometry(raw)


def check(data, stems):
    regions = items = actors = doors = 0
    for stem in stems:
        _, regs, marks = load(data, stem)
        regions += len(regs)
        items += sum(mark.kind == "I" for mark in marks)
        actors += sum(mark.kind == "A" for mark in marks)
        doors += sum(edge_type(r, regs[n]) == "door" for r in regs for n in r[2:6] if n != 0xFFFF)
    if (len(stems), regions, items, actors, doors) != (15, 52669, 663, 1028, 2473):
        raise ValueError("original level or placement census differs")
    return (f"CHECK level schematic: {len(stems)} levels, {regions} regions, {items} items, "
            f"{actors} actor placements, {doors} collapsed portal sides")


def main():
    parser = lol2_cli.tool_args(__doc__, out_help="PNG path outside the repository and original installation")
    parser.add_argument("--level", type=int)
    parser.add_argument("--focus", type=int, metavar="REGION", help="center the map on this zero-based region")
    parser.add_argument("--radius", type=int, default=450, help="map units on each side of a focused region")
    parser.add_argument("--size", type=int, default=1400, help="longest map dimension in pixels")
    args = parser.parse_args()
    if args.check and args.out:
        parser.error("--check prints to stdout")
    if not args.check and (args.level is None or not args.out):
        parser.error("supply --level and --out, or --check")
    if not 540 <= args.size <= 6000 or args.radius < 1:
        parser.error("size must be 540–6000 pixels and radius must be positive")
    try:
        data = Path(args.data).resolve()
        stems = level_files(data)
        if args.check:
            print(check(data, stems))
            return
        stem = next((s for s in stems if int(s.split("_")[0][1:]) == args.level), None)
        if stem is None:
            raise ValueError(f"no archive for level {args.level}")
        out = Path(lol2_cli.refuse_repo_output(args.out)).resolve()
        if out.is_relative_to(data.parent):
            raise ValueError("give an output path outside the game folder")
        if out.suffix.lower() != ".png":
            raise ValueError("--out must name a PNG file")
        image, visible, hidden = draw(stem, *load(data, stem), args.focus, args.radius, args.size)
        out.parent.mkdir(parents=True, exist_ok=True)
        image.save(out)
        print(f"{stem}: {visible} placements, {hidden} crowded labels omitted; wrote {out}")
    except (OSError, ValueError) as error:
        parser.exit(1, f"level schematic: {error}\n")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
