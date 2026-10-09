#!/usr/bin/env python3
"""Make frame-count-checked Theora/Vorbis review clips for the modern engine."""
import argparse,json,struct,subprocess,hashlib
from pathlib import Path

def run(args):
 p=subprocess.run(args,capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr)
 return p

def convert(source,out):
 raw=source.read_bytes();assert raw[:4]==b'FORM' and raw[8:12]==b'WVQA'
 expected,width,height=struct.unpack_from('<HHH',raw,24);fps=raw[32]
 out.parent.mkdir(parents=True,exist_ok=True)
 # All-keyframe encoding avoids Theora duplicate-frame packets being omitted
 # by the review decoder; completeness is verified after conversion.
 p=run(['ffmpeg','-v','error','-y','-i',str(source),'-map','0:v:0','-map','0:a?',
        '-c:v','libtheora','-g','1','-q:v','7','-c:a','libvorbis','-q:a','5',str(out)])
 probe=json.loads(run(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(out)]).stdout)
 video=next(s for s in probe['streams'] if s['codec_type']=='video')
 assert int(video['nb_read_frames'])==expected
 assert (video['width'],video['height'])==(width,height)
 assert abs(float(video['duration'])-expected/fps)<0.001
 report=dict(source=str(source),source_sha256=hashlib.sha256(raw).hexdigest(),output=str(out),
             frames=expected,fps=fps,width=width,height=height,conversion_warning=p.stderr,
             streams=probe['streams'],scope='Lossy engine-readable review conversion with full video frame-count/duration checks. Audio retained at its own source duration, not trimmed to video. No filename binding or story trigger inferred.')
 out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
 print(out,expected,'frames verified')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('out',type=Path)
 a=p.parse_args();convert(a.source,a.out)
