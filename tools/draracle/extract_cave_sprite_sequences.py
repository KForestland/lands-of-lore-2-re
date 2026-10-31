#!/usr/bin/env python3
"""Extract bounded variable-length sprite sequences; identities remain visual candidates."""
import argparse, json, struct
from pathlib import Path
from PIL import Image, ImageDraw
from extract_prop_sprite_previews import decode_rows
from lol2_cache_named_wall_fixture import load_named, require, sha
from lol2_extract_cave_materials import ASSET, HASH
from lol2_wall_material_checkpoint import sections
from lol2_palette_png import rgb_palette


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    _, blob, _, _ = load_named(a.game_root, ASSET)
    require(sha(blob) == HASH, 'Cache changed')
    s = sections(blob)
    paloff = struct.unpack_from('<I', blob, 4)[0]
    pal = rgb_palette(blob[paloff:paloff + 768], 6)
    a.out.mkdir(parents=True, exist_ok=True)
    results = []
    descriptors = [145, 166, 196, 260, 449, 862, 872, 882, 887, 897, 907, 946]
    sheet = Image.new('RGB', (800, 3 * 270), '#444444')
    draw = ImageDraw.Draw(sheet)
    for index, descriptor in enumerate(descriptors):
        v = struct.unpack_from('<6H11I', blob, s[2] + descriptor * 56)
        require(v[3] == 0x2c6 and 1 <= v[4] <= 64, 'Unsupported sequence')
        folder = a.out / str(descriptor)
        folder.mkdir(exist_ok=True)
        for level in range(v[5] & 255):
            pos = s[3] + v[7 + level]
            for variant in range(v[4]):
                size = 8 + struct.unpack_from('<H', blob, pos + 6)[0]
                require(variant != 0 or size == v[12 + level], 'First variant size')
                data = blob[pos:pos + size]
                w, h, pixels, marked = decode_rows(data, 0x2c6)
                require((w, h) == (max(1, v[1] >> level), max(1, v[2] >> level)), 'Dimensions')
                name = f'{descriptor}/variant_{variant}_mip_{level}.png'
                rgba = bytes(c for value in pixels for c in [*pal[value*3:value*3+3], 255 if value else 0])
                im = Image.frombytes('RGBA', (w, h), rgba)
                im.save(a.out / name)
                if level == 0 and variant == 0:
                    im.thumbnail((190, 240), Image.Resampling.NEAREST)
                    x, y = (index % 4) * 200, (index // 4) * 270
                    sheet.paste(im, (x, y + 25), im)
                    draw.text((x + 5, y + 5), str(descriptor), fill='white')
                results.append(dict(descriptor=descriptor, variant=variant, level=level, width=w, height=h, source_offset=pos, payload_sha256=sha(data), png=name))
                pos += size
            if level + 1 < (v[5] & 255):
                require(pos == s[3] + v[8 + level], 'Sequence/mip boundary')
            else:
                # Descriptor aliases can start at later variants in the same sequence.
                following = [s[3] + struct.unpack_from('<I', blob, s[2]+d*56+16)[0] for d in range((s[3]-s[2])//56)]
                require(pos in following, 'Next descriptor boundary')
    sheet.save(a.out / 'contact_sheet.png')
    cards = ''.join(f'<article><h2>Resource {d}</h2><img id="image{d}" src="{d}/variant_0_mip_0.png"><p>Stored variant <output id="value{d}">0</output></p><input aria-label="Resource {d} variant" type="range" min="0" max="{max(r['variant'] for r in results if r['descriptor']==d)}" value="0" oninput="document.getElementById(\'image{d}\').src=\'{d}/variant_\'+this.value+\'_mip_0.png\';document.getElementById(\'value{d}\').value=this.value"></article>' for d in descriptors)
    (a.out / 'review.html').write_text('<!doctype html><meta charset="utf-8"><title>Cave sprite sequences</title><style>body{background:#333;color:white;font:18px sans-serif}main{display:flex;flex-wrap:wrap}article{width:300px;margin:16px}img{image-rendering:pixelated;max-width:290px;max-height:430px;background:#555}input{width:260px}</style><h1>Recovered cave sprite sequences</h1><p>Move each slider to inspect stored variants. These include environmental effects; they are not established enemy sprites. Playback timing and alpha remain provisional.</p><main>'+cards+'</main>')
    report = dict(images=len(results), rows=sum(r['height'] for r in results), results=results, scope='2C6 variable-length row-span sequences; every row, mip and following descriptor boundary checked. File palette, provisional index-zero alpha. Variant order is storage order, not verified animation timing or view selection. No enemy identity or spawn binding claimed.')
    (a.out / 'sequences.json').write_text(json.dumps(report, indent=2)+'\n')
    print({k: v for k, v in report.items() if k != 'results'})


if __name__ == '__main__':
    main()
