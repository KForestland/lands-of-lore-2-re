#!/usr/bin/env python3
"""Extract native 24-byte floor presets and region selectors; resource resolution open."""
import argparse,json,struct,hashlib,html,colorsys
from pathlib import Path
import capstone
from lol2_extract_draracle_geometry import decode,u32
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_spatial_constructor import ConstructorReplay

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 source=(a.game_root/'DAT/L1_DC.MIX').read_bytes();entries,entry,raw,verts,records,regions=decode(source);e=entries[0];meta=source[e['offset']:e['offset']+e['size']]
 start,count=u32(meta,4),u32(meta,0x3c);names=start+count*24
 if names+count*22!=u32(meta,8):raise ValueError('Preset/name boundary mismatch')
 presets=[]
 for k in range(count):
  d=meta[start+k*24:start+(k+1)*24];n=meta[names+k*22:names+(k+1)*22]
  presets.append(dict(index=k,name=n.split(b'\0')[0].decode('ascii'),raw_hex=d.hex(),name_raw_hex=n.hex(),source_offset=e['offset']+start+k*24,resource_index=struct.unpack_from('<h',d,4)[0],scope='Resource index selects native 12-byte table at 0x22d78; direct cache-descriptor equivalence NOT proven.'))
 exe=(a.game_root/'LOLG.DAT').read_bytes()
 if hashlib.sha256(exe).hexdigest()!=EXE_HASH:raise ValueError('Executable changed')
 a.out.mkdir(parents=True,exist_ok=True);md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True;ins={}
 for x,y in [(0x9e037,0x9e05e),(0x67424,0x6745e),(0xb29ca,0xb29d2),(0xb29da,0xb29f1),(0xf64a7,0xf64b2),(0xf64da,0xf64f1),(0xf39fc,0xf3a53)]:
  b=exe[x+0x37000:y+0x37000];ii=list(md.disasm(b,x));ins.update({i.address:i for i in ii});(a.out/f'code_{x:x}.bin').write_bytes(b);(a.out/f'code_{x:x}.txt').write_text('\n'.join(f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in ii)+'\n')
 machine=ConstructorReplay(ins,b'');machine.writemem(0x22d44,4,0x500000);machine.regs['ebp']=0x700000;machine.writemem(0x6ffff8,4,0x600000)
 assigned=[];deferred=[]
 for k,r in enumerate(records):
  index=r[16]&255
  if r[14]&0x20 and not r[14]&0x80:
   deferred.append(dict(region=k,reason='floor subdivision owner; word +32 holds child start'));continue
  if index==255:
   deferred.append(dict(region=k,reason='native absent selector 255'));continue
  if index>=count:raise ValueError(('Preset index out of bounds',k,index))
  machine.mem[0x600000:0x60002c]=bytes.fromhex(regions[k]['raw_hex']);machine.span(0xb29ca,0xb29d2);machine.span(0xb29da,0xb29f1)
  if machine.regs['eax']!=0x500000+index*24:raise ValueError('Native selector replay mismatch')
  assigned.append(dict(region=k,preset=index,name=presets[index]['name']))
 report=dict(presets=presets,region_floor_presets=assigned,deferred=deferred,native_selector_replay_cases=len(assigned),mismatches=0,scope='Named floor preset lookup proven in native consumer; resource-to-cache mapping, ceiling/wall selectors, UVs and shading remain open.')
 (a.out/'floor_presets.json').write_text(json.dumps(report,indent=2)+'\n')
 xs=[x/65536 for x,y in verts];ys=[y/65536 for x,y in verts];colors=['#%02x%02x%02x'%tuple(int(c*255) for c in colorsys.hsv_to_rgb(k/count,.6,.8)) for k in range(count)]
 svg=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min(xs)-50} {min(ys)-50} {max(xs)-min(xs)+100} {max(ys)-min(ys)+100}">']
 for item in assigned:
  pts=' '.join(f'{verts[v][0]/65536},{verts[v][1]/65536}' for v in regions[item['region']]['vertex_indices']);svg.append(f'<polygon points="{pts}" fill="{colors[item["preset"]]}" stroke="#222" stroke-width="2"><title>Region {item["region"]}: {html.escape(item["name"])}</title></polygon>')
 svg.append('</svg>');(a.out/'floor_preset_map.svg').write_text('\n'.join(svg))
 (a.out/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>Cave floor presets</title><style>body{background:#202327;color:white;font:16px sans-serif}aside{position:fixed;width:260px}img{margin-left:280px;width:65%}</style><aside><h1>Native floor presets</h1><p>Colors identify presets, not texture colors. Texture and UV resolution remain open.</p>'+''.join(f'<p style="color:{colors[k]}">{k}: {html.escape(v["name"])}</p>' for k,v in enumerate(presets))+'</aside><img src="floor_preset_map.svg">')
 print(f'{count} named presets; {len(assigned)} native selector replays pass; {len(deferred)} deferred')
if __name__=='__main__':main()
