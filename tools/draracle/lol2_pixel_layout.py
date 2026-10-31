"""Convert original column-major indexed texture pixels to image rows."""
from lol2_cache_named_wall_fixture import require

def column_major_to_rows(data,width,height):
 require(len(data)==width*height,'Pixel extent mismatch')
 return bytes(data[x*height+y] for y in range(height) for x in range(width))

