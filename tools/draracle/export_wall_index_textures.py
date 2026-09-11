#!/usr/bin/env python3
"""Export source palette indices for the existing cave wall review geometry."""
import argparse
import json
import struct
from pathlib import Path
from PIL import Image
from lol2_cache_named_wall_fixture import load_named, require, sha
from lol2_extract_cave_materials import ASSET, HASH
from lol2_wall_material_checkpoint import sections
from lol2_pixel_layout import column_major_to_rows
from lol2_palette_png import rgb_palette


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root', type=Path, required=True)
    p.add_argument('--wall-assets', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    _, blob, _, _ = load_named(a.game_root, ASSET)
    require(sha(blob) == HASH, 'Cache changed')
    s = sections(blob)
    palette_offset = struct.unpack_from('<I', blob, 4)[0]
    palette = rgb_palette(blob[palette_offset:palette_offset + 768], 6)
    walls = json.loads((a.wall_assets / 'walls.json').read_text())['walls']
    a.out.mkdir(parents=True, exist_ok=True)
    records = []
    for descriptor in sorted({int(w['descriptor']) for w in walls}):
        v = struct.unpack_from('<6H11I', blob, s[2] + descriptor * 56)
        width, height, flags = v[1:4]
        require(flags in (0xa9, 0x80a9, 0xc3, 0xe1, 0x80e1, 0x8b), 'Unknown preview layout')
        require(v[12] == 8 + width * height, 'Non-raw mip')
        pos = s[3] + v[7]
        require(struct.unpack_from('<4H', blob, pos) ==
                (flags, width, height, (width * height) & 65535), 'Mip header changed')
        raw = blob[pos + 8:pos + v[12]]
        indices = column_major_to_rows(raw, width, height) if flags in (0xa9, 0x80a9) else raw
        # Independent parity with the already reviewed RGB texture prevents
        # changing orientation, variant or palette during the new export.
        rgb = bytes(c for index in indices for c in palette[index * 3:index * 3 + 3])
        reference = Image.open(a.wall_assets / f'material_{descriptor}_variant_0.png').convert('RGB')
        require(reference.size == (width, height) and reference.tobytes() == rgb,
                'Existing reviewed texture differs')
        Image.frombytes('L', (width, height), indices).save(a.out / f'material_{descriptor}.png')
        records.append(dict(descriptor=descriptor, width=width, height=height,
                            row_major_indices_sha256=sha(indices), rgb_parity=True,
                            layout_scope="column-major" if flags in (0xa9, 0x80a9) else "existing row-major preview, native layout unverified"))
    Image.frombytes('RGB', (256, 1), palette).save(a.out / 'palette.png')
    report = dict(cache_sha256=HASH, walls=len(walls), materials=records,
                  scope='Original variant0 indices; exact RGB parity with current wall assets. Geometry, UVs and orientation unchanged. No runtime shade assignment.')
    (a.out / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Exported {len(records)} indexed materials for {len(walls)} wall spans; RGB parity exact')


if __name__ == '__main__':
    main()
