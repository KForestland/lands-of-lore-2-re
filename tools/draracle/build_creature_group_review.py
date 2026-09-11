#!/usr/bin/env python3
"""Validate stored block-sprite groups and build a diagnostic playback viewer."""
import argparse,json,struct
from pathlib import Path
from lol2_cache_named_wall_fixture import load_named,require,sha
from lol2_extract_cave_materials import ASSET,HASH
from lol2_wall_material_checkpoint import sections


def group_frames(descriptors):
    groups={}
    for ordinal,v in descriptors.items():
        count,index=v[4]&255,v[4]>>8
        require(0<=index<count,'Invalid group ordinal')
        base=ordinal-index
        groups.setdefault(base,[]).append((index,ordinal,v))
    result=[]
    for base,rows in sorted(groups.items()):
        rows.sort();first=rows[0][2];count=first[4]&255
        require([r[0] for r in rows]==list(range(count)),'Incomplete group')
        for index,ordinal,v in rows:
            require(ordinal==base+index and v[0]==first[0]+index,'Resource sequence')
            require(v[1:4]==first[1:4] and v[6]==first[6] and v[4]&255==count,'Group identity mismatch')
        result.append(dict(base=base,count=count,name_hash_candidate=first[6],frames=[r[1] for r in rows]))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--frames',type=Path,required=True);a=p.parse_args()
    _,blob,_,_=load_named(a.game_root,ASSET);require(sha(blob)==HASH,'Cache changed');s=sections(blob)
    descriptors={d:struct.unpack_from('<6H11I',blob,s[2]+d*56) for d in range((s[3]-s[2])//56)}
    groups=group_frames({d:v for d,v in descriptors.items() if v[3]==0x1246})
    for g in groups:
        for d in g['frames']:require((a.frames/f'frame_{d}.png').is_file(),'Decoded PNG missing')
    (a.frames/'groups.json').write_text(json.dumps(dict(groups=groups,scope='Source grouping by packed count/index, contiguous resource IDs and shared hash/dimensions. Not named creature states, direction semantics, playback rate or live runtime proof.'),indent=2)+'\n')
    page='''<!doctype html><meta charset="utf-8"><title>Cave creature frame groups</title><style>body{background:#292929;color:white;font:18px sans-serif;margin:24px}button,select,input{font:inherit;margin:8px}img{background:#444;image-rendering:pixelated;max-width:100%}#position{width:75%}</style><h1>Recovered creature frame groups</h1><p>Choose a stored group, then step through its poses. Playback speed is a review setting; original timing, state names and spawn locations remain unverified.</p><label>Group <select id="group"></select></label><p><button id="prev">Previous frame</button><button id="play">Play preview</button><button id="next">Next frame</button><label>Preview FPS <input id="fps" type="number" min="1" max="30" value="6"></label></p><input aria-label="Frame in group" id="position" type="range" min="0" value="0"><p id="label"></p><img id="image"><script>const groups=DATA;const select=document.getElementById('group'),position=document.getElementById('position'),play=document.getElementById('play');let timer=null;for(const g of groups){const o=document.createElement('option');o.value=g.base;o.textContent='Resource '+g.base+' — '+g.count+' frames';select.appendChild(o)}function current(){return groups.find(g=>g.base===Number(select.value))}function show(){const g=current(),i=Number(position.value);document.getElementById('image').src='frame_'+g.frames[i]+'.png';document.getElementById('label').textContent='Resource '+g.frames[i]+' · frame '+(i+1)+' / '+g.count}function stop(){clearInterval(timer);timer=null;play.textContent='Play preview'}function step(n){position.value=(Number(position.value)+n+current().count)%current().count;show()}select.onchange=()=>{stop();position.max=current().count-1;position.value=0;show()};position.oninput=()=>{stop();show()};document.getElementById('prev').onclick=()=>{stop();step(-1)};document.getElementById('next').onclick=()=>{stop();step(1)};play.onclick=()=>{if(timer){stop();return}const fps=Math.max(1,Math.min(30,Number(document.getElementById('fps').value)||6));timer=setInterval(()=>step(1),1000/fps);play.textContent='Pause'};document.getElementById('fps').onchange=stop;select.onchange();</script>'''
    (a.frames/'groups.html').write_text(page.replace('DATA',json.dumps(groups)))
    print(dict(groups=len(groups),frames=sum(g['count'] for g in groups)))


if __name__=='__main__':main()
