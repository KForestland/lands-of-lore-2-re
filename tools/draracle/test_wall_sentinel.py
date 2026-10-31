import unittest
from lol2_verify_flat_wall_spans import WallReplay

class SentinelTests(unittest.TestCase):
    def test_absent_region_reads_rejected(self):
        machine=WallReplay({},bytes(44))
        base=0x400000+65535*44
        for address,size in [(base,2),(base+28,2),(base-1,2),(base+43,2)]:
            with self.subTest(address=address):
                with self.assertRaisesRegex(ValueError,'Absent-neighbor'):
                    machine.readmem(address,size)
    def test_real_region_remains_readable(self):
        machine=WallReplay({},bytes([7])*44)
        self.assertEqual(machine.readmem(0x400000+28,2),0x0707)
