"""Native wall texel addressing for bounded, non-overflow 16.16 inputs.

Coordinates are pre-addressing renderer results, not world-space or normalized UVs.
"""
def address_uv(u,v,u_offset,v_offset,mip,width,height,flags):
    if not (0<=mip<=4 and width>0 and height>0 and 0<=u_offset<=255 and 0<=v_offset<=255):
        raise ValueError('Invalid wall texture addressing inputs')
    if not all(-(1<<31)<=x<(1<<31) for x in [u,v]):
        raise ValueError('Coordinate outside signed 32-bit domain')
    clamp=lambda x,size:max(0,min(x,(size<<16)-1))
    if flags&8:
        x=max(u,0)+(u_offset<<16);y=max(v,0)+(v_offset<<16)
        if max(x,y)>=1<<31:raise ValueError('Overflow domain not verified')
        return (x>>mip)%(width<<16),(y>>mip)%(height<<16)
    if flags&16:
        x=max(u,0)+(u_offset<<16)
        if x>=1<<31:raise ValueError('Overflow domain not verified')
        return (x>>mip)%(width<<16),clamp(v>>mip,height)
    return clamp(u>>mip,width),clamp(v>>mip,height)
