#!/usr/bin/env python3
"""Replay native descriptor mip-resource indexing for extracted wall materials."""
import argparse,json,struct
from pathlib import Path
import capstone
from lol2_cache_named_wall_fixture import load_named,require,sha
from lol2_extract_cave_materials import ASSET,HASH
from lol2_wall_material_checkpoint import sections
from lol2_verify_draracle_slopes import EXE_HASH
from lol2_verify_spatial_constructor import ConstructorReplay

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--textures',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 _,blob,_,_=load_named(a.game_root,ASSET);require(sha(blob)==HASH,'Cache changed');s=sections(blob)
 exe=(a.game_root/'LOLG.DAT').read_bytes();require(sha(exe)==EXE_HASH,'Executable changed')
 code=exe[0x1326fa+0x37000:0x13270b+0x37000];md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
 ins={i.address:i for i in md.disasm(code,0x1326fa)};m=ConstructorReplay(ins,b'');results=[]
 report=json.loads(a.textures.read_text())
 for material in report['materials']:
  k=material['descriptor'];prefix=blob[s[2]+k*56:s[2]+k*56+12];ident=struct.unpack_from('<H',prefix)[0];variants=prefix[8]
  for level in sorted({im['level'] for im in material['images']}):
   m.mem[0x500000:0x50000c]=prefix;m.writemem(0x600000,4,level);m.regs.update(esi=0x500000,ebx=0x600000)
   m.span(0x1326fa,0x132701)
   i=ins[0x132701];require(i.mnemonic=='imul' and len(i.operands)==2,'Unexpected multiply')
   m.put(i,i.operands[0],m.get(i,i.operands[0])*m.get(i,i.operands[1]))
   m.span(0x132704,0x13270b);expected=ident+level*variants
   require(m.regs['ecx']==expected,'Native mip resource ID mismatch')
   results.append(dict(descriptor=k,mip=level,resource_id=expected))
 a.out.mkdir(parents=True,exist_ok=True)
 (a.out/'mip_ids.json').write_text(json.dumps(dict(cases=len(results),mismatches=0,results=results,scope='Original 1326FA..13270B indexing instructions with supplied compact descriptors. Base resource ID for each mip, not animation variant selection or UV proof.'),indent=2))
 print(len(results),'native mip ID cases pass')
if __name__=='__main__':main()
