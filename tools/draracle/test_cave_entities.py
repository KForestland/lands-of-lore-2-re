import struct
import unittest
from catalogue_cave_entities import partition_entities

class EntityPartitionTests(unittest.TestCase):
    def record(self, count, offset, extra=0):
        r = bytearray(147)
        r[46], r[47] = count, extra
        struct.pack_into('<I',r,55,offset)
        r[135:140] = b'WORM\0'
        return r

    def test_high_byte_is_not_part_of_count(self):
        rows = partition_entities(self.record(2,0,1)+self.record(1,8), bytes(range(12)))
        self.assertEqual(rows[1]['entries_bytes'], [[8,9,10,11]])
        self.assertEqual(rows[0]['entry_count'],2)

    def test_overlapping_partition_rejected(self):
        with self.assertRaises(ValueError):
            partition_entities(self.record(2,0)+self.record(1,4),bytes(12))

    def test_unclaimed_tail_rejected(self):
        with self.assertRaises(ValueError):
            partition_entities(self.record(1,0),bytes(8))
