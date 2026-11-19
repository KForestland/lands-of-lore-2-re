#!/usr/bin/env python3
"""Bind nonnegative native floor preset references to cache descriptor ordinals."""
import argparse,json,struct,hashlib,html
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import load_named,require,sha
from lol2_extract_cave_materials import ASSET,HASH
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_spatial_constructor import ConstructorReplay

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--presets',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 _,blob,identity,_=load_named(a.game_root,ASSET);require(sha(blob)==HASH,'Cache changed')
 start,size,count=(struct.unpack_from('<I',blob,x)[0] for x in [0x10,0x4c,0x2a8]);require(size==count*56,'Native descriptor count mismatch')
 table=b''.join(blob[start+i*56:start+i*56+12] for i in range(count));require(len(table)==count*12,'Compact table extent')
 exe=(a.game_root/'LOLG.DAT').read_bytes();require(sha(exe)==EXE_HASH,'Executable changed');a.out.mkdir(parents=True,exist_ok=True)
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True;ins={};proof=[]
 for x,y in [(0x9dc17,0x9dc90),(0x1548d8,0x15491d),(0xf64a7,0xf64b2),(0xf64da,0xf64f1)]:
  b=exe[x+0x37000:y+0x37000];ii=list(md.disasm(b,x));ins.update({i.address:i for i in ii});(a.out/f'code_{x:x}.bin').write_bytes(b);(a.out/f'code_{x:x}.txt').write_text('\n'.join(f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in ii)+'\n');proof.append(dict(va=hex(x),file_offset=x+0x37000,sha256=sha(b)))
 r=ConstructorReplay(ins,b'');r.mem[0x500000:0x500000+len(table)]=table;r.writemem(0x22d78,4,0x500000);r.regs['esp']=0x700000;r.writemem(0x700000,4,0)
 presets=json.loads(a.presets.read_text());bindings=[]
 for preset in presets['presets']:
  k=preset['resource_index'];d=bytes.fromhex(preset['raw_hex']);r.mem[0x600000:0x600018]=d;r.regs['esi']=0x600000;r.span(0xf64a7,0xf64b2)
  if k<0:
   bindings.append(dict(preset=preset['index'],name=preset['name'],animated_reference=k,status='animation table unresolved'));continue
  require(k<count,'Preset outside descriptors');require(r.regs['eax']==k,'Native signed reference mismatch');r.regs['edx']=k;r.span(0xf64da,0xf64f1)
  require(r.regs['eax']==0x500000+k*12,'Native resource indexing mismatch')
  prefix=bytes(r.mem[r.regs['eax']:r.regs['eax']+12]);require(prefix==blob[start+k*56:start+k*56+12],'Descriptor prefix differs')
  bindings.append(dict(preset=preset['index'],name=preset['name'],descriptor_index=k,descriptor_header_hex=prefix.hex(),flags=struct.unpack_from('<H',prefix,6)[0],status='native static descriptor binding'))
 byid={b['preset']:b for b in bindings};regions=[]
 for item in presets['region_floor_presets']:
  b=byid[item['preset']];regions.append(dict(**item,descriptor_index=b.get('descriptor_index'),status=b['status']))
 report=dict(identity=identity,code=proof,descriptor_count=count,compact_table_sha256=sha(table),bindings=bindings,regions=regions,deferred=presets['deferred'],native_index_replay_cases=sum('descriptor_index' in b for b in bindings),scope='Loader copy loop and copy direction verified by disassembly; preset index arithmetic replayed. Full loader/copy routine not emulated. UVs and lighting are unresolved.')
 (a.out/'bindings.json').write_text(json.dumps(report,indent=2)+'\n');(a.out/'compact_resource_table.bin').write_bytes(table)
 rows=''.join('<tr><td>'+str(b['preset'])+'</td><td>'+html.escape(b['name'])+'</td><td>'+str(b.get('descriptor_index','animated'))+'</td><td>'+html.escape(b['status'])+'</td></tr>' for b in bindings)
 (a.out/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>Cave material bindings</title><style>body{background:#222;color:#eee;font:16px sans-serif;margin:30px}td,th{padding:10px;border-bottom:1px solid #555}</style><h1>Native cave floor material bindings</h1><p>Static texture identity is resolved. Texture orientation, UV scaling and in-game lighting still require verification.</p><table><tr><th>Preset</th><th>Original name</th><th>Cache descriptor</th><th>Evidence</th></tr>'+rows+'</table>')
 print('Bindings:',[(b['name'],b.get('descriptor_index','animated')) for b in bindings]);print('Native index replay:',report['native_index_replay_cases'])
if __name__=='__main__':main()
