#!/usr/bin/env python3
"""Decoder for Westwood VQA v2 movies with partial codebooks, as used by Lands of Lore II.

This is a Python reimplementation, not an execution of the original player. Its rules come from the original data and
loader evidence:
- The swap rule: the codebook assembled from N partial parts (N = VQHD byte 13) replaces the current one after the frame
  carrying the N-th part, i.e. from the next frame on. The original loader (LOLG.DAT 1.30, cited at 0x171168) counts
  the parts against VQHD byte 13 and publishes the completed buffer.
- Pointers: hi byte 0xFF is a solid block of colour lo; otherwise the vector is hi*256+lo.
- Palette: CPL0 is 6-bit, expanded (v<<2)|(v>>4), the same expansion FFmpeg uses.

Top-level VQFL chunks are seek snapshots: a full CBFZ codebook plus the partial parts of the group in progress, for
jumping to loop/segment starts. The original loader only takes them with load flag 0x20 (cited at LOLG 0x16E2B9), so
linear playback ignores them. FFmpeg's demuxer instead appends each VQFL to the next VQFR packet, and its decoder keeps
the last CBPZ per packet, replacing that frame's own part. The next codebook group is then corrupted. See
docs/lol2-vqa-v2.md.

Input handling is strict:
- Malformed or truncated data raises VQAError.
- Variants this decoder was not validated on also raise VQAError, as unsupported: other VQA versions, other block
  sizes, CBF0/CBP0/VPT0/CPLZ and unknown frame sub-chunks.
- partial_v2() validates the container, header and frame count before classification. Non-partial movies are left to
  another decoder (for example FFmpeg), which handles them correctly.

Requires Python 3.10+ and NumPy. Pillow is needed only for --out (PNG frames).

    python3 tools/lol2_vqa_v2_decode.py MOVIE.VQA --out frames/
    python3 tools/lol2_vqa_v2_decode.py ./lol2_game/DAT/CHUT.MIX            # list VQA entries
    python3 tools/lol2_vqa_v2_decode.py ./lol2_game/DAT/CHUT.MIX --entry 3 --out frames/
"""
import argparse
import sys
from pathlib import Path

import numpy as np


class VQAError(ValueError):
    """Malformed or unsupported VQA input."""

VQHD_SIZE=42
FRAME_TAGS={b'CBFZ',b'CBPZ',b'CPL0',b'VPTZ'}
UNSUPPORTED_FRAME_TAGS={b'CBF0',b'CBP0',b'VPT0',b'CPLZ',b'VPRZ',b'VPTR',b'VPTD',b'VPTK'}

def chunks(data: bytes, start: int=0, end: int|None=None, where: str='file') -> list:
    """IFF chunks (4-byte tag, big-endian u32 size, payload, pad to even) between start and end, bounds-checked."""
    end=len(data) if end is None else end
    out=[];i=start
    while i<end:
        if end-i<8: raise VQAError(f'{where}: truncated chunk header at {i}')
        tag=bytes(data[i:i+4]);size=int.from_bytes(data[i+4:i+8],'big')
        if not all(0x20<=c<0x7f for c in tag): raise VQAError(f'{where}: invalid chunk tag {tag!r} at {i}')
        body=i+8
        if size>end-body: raise VQAError(f'{where}: chunk {tag.decode()} size {size} exceeds data at {i}')
        out.append((tag,bytes(data[body:body+size])))
        i=body+size+(size&1)
    if i>end: raise VQAError(f'{where}: chunk padding overruns data')
    return out

def lcw(src: bytes) -> bytes:
    """Strict Westwood LCW (Format80): every read and back-reference is bounds-checked; the stream must end with 0x80."""
    d=bytearray();i=0;n=len(src)
    def need(k):
        if i+k>n: raise VQAError(f'LCW: truncated command at {i}')
    while True:
        need(1);op=src[i];i+=1
        if op==0x80: return bytes(d)
        if op<0x80:
            need(1);count=((op&0x70)>>4)+3;off=((op&0x0F)<<8)|src[i];i+=1;s=len(d)-off
            if off==0 or s<0: raise VQAError(f'LCW: relative reference {off} outside output at {i}')
        elif op<0xC0:
            count=op&0x3F;need(count);d+=src[i:i+count];i+=count;continue
        elif op==0xFE:
            need(3);count=src[i]|src[i+1]<<8;d+=bytes([src[i+2]])*count;i+=3;continue
        else:
            if op==0xFF: need(4);count=src[i]|src[i+1]<<8;s=src[i+2]|src[i+3]<<8;i+=4
            else: need(2);count=(op&0x3F)+3;s=src[i]|src[i+1]<<8;i+=2
            if s>=len(d): raise VQAError(f'LCW: absolute reference {s} outside output ({len(d)}) at {i}')
        for k in range(count): d.append(d[s+k])

def header(blob: bytes) -> tuple:
    """(top-level chunks, VQHD fields) for a WVQA FORM; VQAError if malformed."""
    if len(blob)<12 or blob[:4]!=b'FORM': raise VQAError('not an IFF FORM')
    size=int.from_bytes(blob[4:8],'big')
    if size<4 or size+8>len(blob): raise VQAError(f'FORM size {size} exceeds file ({len(blob)})')
    if blob[8:12]!=b'WVQA': raise VQAError('FORM type is not WVQA')
    top=chunks(blob,12,8+size,'FORM')
    hd=[pl for t,pl in top if t==b'VQHD']
    if len(hd)!=1: raise VQAError(f'expected one VQHD, found {len(hd)}')
    hd=hd[0]
    if len(hd)!=VQHD_SIZE: raise VQAError(f'VQHD is {len(hd)} bytes, expected {VQHD_SIZE}')
    f=dict(version=int.from_bytes(hd[0:2],'little'),frames=int.from_bytes(hd[4:6],'little'),width=int.from_bytes(hd[6:8],'little'),
        height=int.from_bytes(hd[8:10],'little'),block_w=hd[10],block_h=hd[11],fps=hd[12],parts=hd[13])
    count=sum(t==b'VQFR' for t,_ in top)
    if count!=f['frames']: raise VQAError(f"VQFR frame count {count} does not match VQHD frame count {f['frames']}")
    return top,f

def _supported(f: dict) -> None:
    if f['version']!=2: raise VQAError(f"unsupported VQA version {f['version']}")
    if (f['block_w'],f['block_h'])!=(4,4): raise VQAError(f"unsupported block size {f['block_w']}x{f['block_h']}")
    if f['width']<=0 or f['height']<=0 or f['width']%4 or f['height']%4: raise VQAError(f"invalid frame size {f['width']}x{f['height']}")
    if f['parts']<1: raise VQAError('VQHD partial-codebook part count is 0')

def partial_v2(blob: bytes) -> bool:
    """Classify after container/header/frame-count validation. True for VQA v2 (4x4) with partial codebooks;
    False delegates non-partial compressed-frame validation and decoding to FFmpeg."""
    top,f=header(blob)
    frames_=[pl for t,pl in top if t==b'VQFR']
    tags=set()
    for i,pl in enumerate(frames_): tags|={t for t,_ in chunks(pl,where=f'VQFR {i}')}
    if not tags&{b'CBPZ',b'CBP0'}: return False
    _supported(f)
    return True

def frames(blob: bytes):
    """Yield RGB frames (H, W, 3 uint8) for linear playback. VQFL seek snapshots and audio/info chunks are skipped."""
    top,f=header(blob);_supported(f)
    w,h,per=f['width'],f['height'],f['parts'];gx,gy=w//4,h//4;n=gx*gy
    vqfr=[pl for t,pl in top if t==b'VQFR']
    if not vqfr: raise VQAError('no VQFR frames')
    cb=None;pal=None;pending=b'';k=0
    for fi,pl in enumerate(vqfr):
        sub=chunks(pl,where=f'VQFR {fi}')
        seen=set()
        for t,_ in sub:
            if t in UNSUPPORTED_FRAME_TAGS: raise VQAError(f'VQFR {fi}: unsupported sub-chunk {t.decode()}')
            if t not in FRAME_TAGS: raise VQAError(f'VQFR {fi}: unknown sub-chunk {t!r}')
            if t in seen: raise VQAError(f'VQFR {fi}: duplicate sub-chunk {t.decode()}')
            seen.add(t)
        parts=dict(sub)
        if b'CPL0' in parts:
            if len(parts[b'CPL0'])!=768: raise VQAError(f"VQFR {fi}: CPL0 is {len(parts[b'CPL0'])} bytes, expected 768")
            p=np.frombuffer(parts[b'CPL0'],np.uint8).astype(np.uint16)&63
            pal=((p<<2)|(p>>4)).astype(np.uint8).reshape(-1,3)
        if b'CBFZ' in parts:
            book=lcw(parts[b'CBFZ'])
            if not book or len(book)%16: raise VQAError(f'VQFR {fi}: full codebook is {len(book)} bytes (not whole 4x4 vectors)')
            cb=np.frombuffer(book,np.uint8)
        if pal is None: raise VQAError(f'VQFR {fi}: no palette before the first rendered frame')
        if cb is None: raise VQAError(f'VQFR {fi}: no codebook before the first rendered frame')
        if b'VPTZ' not in parts: raise VQAError(f'VQFR {fi}: missing VPTZ')
        v=lcw(parts[b'VPTZ'])
        if len(v)!=2*n: raise VQAError(f'VQFR {fi}: VPTZ decodes to {len(v)} bytes, expected {2*n}')
        lo=np.frombuffer(v[:n],np.uint8).astype(np.int64);hi=np.frombuffer(v[n:2*n],np.uint8).astype(np.int64)
        solid=hi==0xff;nvec=len(cb)//16;index=hi*256+lo
        if (index[~solid]>=nvec).any(): raise VQAError(f'VQFR {fi}: vector {int(index[~solid].max())} outside codebook of {nvec}')
        table=cb.reshape(nvec,4,4)
        blocks=np.where(solid[:,None,None],lo[:,None,None].astype(np.uint8),table[np.where(solid,0,index)])
        yield pal[blocks.reshape(gy,gx,4,4).transpose(0,2,1,3).reshape(h,w)]
        if b'CBPZ' in parts:
            pending+=parts[b'CBPZ'];k+=1
            if k==per:
                book=lcw(pending)
                if not book or len(book)%16: raise VQAError(f'VQFR {fi}: partial codebook is {len(book)} bytes (not whole 4x4 vectors)')
                cb=np.frombuffer(book,np.uint8);pending=b'';k=0

def save_frames(blob: bytes, folder: Path) -> int:
    """Write %04d.png frames (1-based) for a partial-codebook VQA v2. Returns the frame count."""
    from PIL import Image
    folder.mkdir(parents=True, exist_ok=True)
    count = 0
    for i, rgb in enumerate(frames(blob)):
        Image.fromarray(rgb).save(folder / f'{i + 1:04d}.png')
        count += 1
    return count


def _mix_entries(data: bytes):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lol2_source_format import parse_mix
    return parse_mix(data)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Decode LoL2 partial-codebook VQA v2 movies (see docs/lol2-vqa-v2.md).')
    ap.add_argument('path', type=Path, help='a .VQA file, or a MIX archive holding VQA entries (read only)')
    ap.add_argument('--entry', type=int, help='MIX entry index to decode')
    ap.add_argument('--key', type=lambda s: int(s, 0), help='MIX entry key (hash) to decode')
    ap.add_argument('--out', type=Path, help='write PNG frames here (needs Pillow)')
    a = ap.parse_args(argv)
    data = a.path.read_bytes()
    if data[:4] == b'FORM':
        blobs = [('file', data)]
    else:
        entries = _mix_entries(data)
        if a.entry is not None or a.key is not None:
            hit = [e for e in entries if e['index'] == a.entry or e['key'] == a.key]
            if len(hit) != 1:
                ap.error('entry not found')
            e = hit[0]
            blobs = [(f"entry {e['index']} key {e['key']:#010x}", data[e['offset']:e['offset'] + e['size']])]
        else:
            blobs = [(f"entry {e['index']} key {e['key']:#010x}", data[e['offset']:e['offset'] + e['size']])
                     for e in entries if data[e['offset'] + 8:e['offset'] + 12] == b'WVQA']
    status = 0
    for name, blob in blobs:
        try:
            _, f = header(blob)
            partial = partial_v2(blob)
        except VQAError as error:
            print(f'{name}: VQAError: {error}')
            status = 1
            continue
        kind = 'partial-codebook v2 (this decoder)' if partial else 'not partial (use another decoder)'
        print(f"{name}: v{f['version']} {f['width']}x{f['height']} {f['frames']} frames, "
              f"{f['fps']} fps, parts {f['parts']}: {kind}")
        if a.out is not None and len(blobs) == 1:
            if not partial:
                ap.error('this movie has no partial codebooks; decode it with another decoder')
            print(f'wrote {save_frames(blob, a.out)} frames to {a.out}')
    if a.out is not None and len(blobs) != 1:
        ap.error('--out needs a single movie (give --entry or --key for a MIX)')
    return status


if __name__ == '__main__':
    sys.exit(main())
