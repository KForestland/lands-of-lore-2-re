import struct
import unittest
from extract_block_sprite_frames import decode_blocks,lcw

class BlockSpriteTests(unittest.TestCase):
    def frame(self,index=0,count=1):
        data=bytearray(24)
        data.extend(struct.pack('<HBBH',2,1,count,index))
        struct.pack_into('<4H',data,0,0x1246,4,4,len(data)-22)
        return data

    def test_four_rows_keep_codebook_order(self):
        self.assertEqual(decode_blocks(self.frame(),bytes(range(16)))[2],bytes(range(16)))

    def test_invalid_index_rejected(self):
        with self.assertRaises(ValueError):decode_blocks(self.frame(1),bytes(16))

    def test_run_overflow_rejected(self):
        with self.assertRaises(ValueError):decode_blocks(self.frame(count=2),bytes(16))

    def test_lcw_overlapping_copy(self):
        self.assertEqual(lcw(bytes([0x81,7,0,1,0x80])),bytes([7]*4))

    def test_lcw_bad_reference(self):
        with self.assertRaises(ValueError):lcw(bytes([0,1,0x80]))
