#!/usr/bin/env python3
"""Extract structurally validated A9 cave textures; no geometry/lighting assignments."""
import argparse,base64,collections,html,json,struct
from pathlib import Path
from lol2_cache_named_wall_fixture import load_named,sha,require
from lol2_wall_material_checkpoint import sections,material_record
from lol2_pixel_layout import column_major_to_rows
from lol2_palette_png import rgb_palette,colorize,png_rgb
ASSET='sphere1\\l1_dc\\l1_dc.tex'
HASH='102410e0b69037da2bdf451dd4de9c7e30df2c9d1309b1d0a1c0224ab7218c97'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 record,b,identity,_=load_named(a.game_root,ASSET);require(sha(b)==HASH,'Unsupported cave blob')
 s=sections(b);pal=struct.unpack_from('<I',b,4)[0]
 require(pal+768==s[4],'Palette boundary');dac=b[pal:pal+768];rgb=rgb_palette(dac,6)
 require((s[5]-s[4])%256==0,'Shade table boundary');shade=b[s[4]:s[5]];banks=len(shade)//256
 require((s[3]-s[2])%56==0,'Descriptor boundary');count=(s[3]-s[2])//56
 good=[];rejected=[];cards=[];viewer=[];a.out.mkdir(parents=True,exist_ok=True)
 for k in range(count):
  try:r=material_record(b,k,allow_partial_mips=True)
  except ValueError as e:
   rejected.append(dict(index=k,flags=struct.unpack_from('<H',b,s[2]+k*56+6)[0],reason=str(e)));continue
  folder=a.out/f'material_{k:04d}';folder.mkdir(exist_ok=True)
  (folder/'descriptor.bin').write_bytes(b[r['descriptor_start']:r['descriptor_start']+56])
  for m in r['mips']:
   pixels=b[m['data_start']:m['data_start']+m['width']*m['height']]
   (folder/f'mip_{m["level"]}.indices').write_bytes(pixels)
   (folder/f'mip_{m["level"]}_palette.png').write_bytes(png_rgb(m['width'],m['height'],colorize(column_major_to_rows(pixels,m["width"],m["height"]),rgb)))
  good.append(r);m=r['mips'][0];pixels=b[m['data_start']:m['data_start']+m['width']*m['height']]
  viewer.append(dict(index=k,width=m['width'],height=m['height'],pixels=base64.b64encode(column_major_to_rows(pixels,m["width"],m["height"])).decode()))
  cards.append(f'<article><h2>Descriptor {k} · {m["width"]} × {m["height"]}</h2><canvas id="m{k}" width="{m["width"]}" height="{m["height"]}"></canvas><p><a href="material_{k:04d}/mip_0_palette.png">Palette PNG</a></p></article>')
 (a.out/'palette_dac.bin').write_bytes(dac);(a.out/'shade_rows.bin').write_bytes(shade)
 report=dict(asset=ASSET,identity=identity,record=record,descriptor_count=count,extracted_count=len(good),mip_count=sum(len(r["mips"]) for r in good),palette_offset=pal,shade_offset=s[4],shade_banks=banks,materials=good,rejected=rejected,scope='Structural extraction using previously witnessed A9 layout. Column-major source pixels converted to row-major file-palette previews; no cave runtime color replay, material names, geometry bindings or dynamic lighting assignments.')
 (a.out/'materials.json').write_text(json.dumps(report,indent=2)+'\n')
 page='''<!doctype html><meta charset="utf-8"><title>Draracle cave materials</title><style>body{background:#202327;color:#eee;font:16px sans-serif;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}article{background:#30353b;padding:16px}h2{font-size:16px}canvas{image-rendering:pixelated;max-width:100%;max-height:256px}a{color:#9df}header{position:sticky;top:0;background:#202327;padding:12px;z-index:1}</style><header><h1>Original Draracle cave texture candidates</h1><p>26 structurally validated materials. Geometry bindings and live lighting remain unverified.</p><label><input id="shaded" type="checkbox"> Apply a file shade row</label> <input id="bank" type="range" min="0" max="65" value="0"><output id="value">0</output><p>Unchecked: direct file palette. Checked: diagnostic shade-row preview, not assigned scene lighting.</p></header><main>'''+''.join(cards)+'''</main><script>const materials='''+json.dumps(viewer)+''';const palette='''+json.dumps(list(rgb))+''';const shades='''+json.dumps(list(shade))+''';for(const m of materials)m.data=Uint8Array.from(atob(m.pixels),c=>c.charCodeAt(0));function draw(){const bank=Number(document.getElementById('bank').value),on=document.getElementById('shaded').checked;document.getElementById('value').textContent=bank;for(const m of materials){const c=document.getElementById('m'+m.index).getContext('2d'),im=c.createImageData(m.width,m.height);for(let i=0;i<m.data.length;i++){let v=m.data[i];if(on)v=shades[bank*256+v];im.data.set([palette[v*3],palette[v*3+1],palette[v*3+2],255],i*4)}c.putImageData(im,0,0)}}document.getElementById('bank').oninput=draw;document.getElementById('shaded').onchange=draw;draw();</script>'''
 (a.out/'review.html').write_text(page)
 print(json.dumps({k:report[k] for k in ['descriptor_count','extracted_count','mip_count','shade_banks']}))
if __name__=='__main__':main()
