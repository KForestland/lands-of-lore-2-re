import struct
import unittest
from lol2_extract_draracle_geometry import parse_mix, decode, slope_corners

class GeometryTests(unittest.TestCase):
    def region(self,floor,ceiling):
        r=[0]*22;r[2:6]=[65535]*4;r[10]=floor&65535;r[11]=ceiling&65535;return r
    def test_flat_signed_heights(self):
        r=self.region(-300,120)
        self.assertEqual(slope_corners([r],0),[-300]*4)
        self.assertEqual(slope_corners([r],0,True),[120]*4)
    def test_neighbor_floor_and_ceiling_directions(self):
        for ceiling in [False,True]:
            for side in range(4):
                r=self.region(-300,120);n=self.region(-200,250)
                r[2+side]=1;r[14]=(8 if ceiling else 4)|(side<<(14 if ceiling else 12))
                expected=[120 if ceiling else -300]*4
                expected[side]=expected[(side+1)%4]=250 if ceiling else -200
                self.assertEqual(slope_corners([r,n],0,ceiling),expected)
    def test_missing_neighbor_uses_opposite_height(self):
        r=self.region(-300,120);r[14]=4
        self.assertEqual(slope_corners([r],0),[120,120,-300,-300])
        r[14]=8|(2<<14)
        self.assertEqual(slope_corners([r],0,True),[120,120,-300,-300])
    def test_slope_invalid_neighbor_rejected(self):
        r=self.region(0,100);r[14]=4;r[2]=9
        with self.assertRaises(ValueError):slope_corners([r],0)
    def test_mix_bounds_and_overlap(self):
        good=struct.pack('<HI',1,3)+struct.pack('<III',1,0,3)+b'abc'
        self.assertEqual(parse_mix(good)[0]['offset'],18)
        for invalid in [b'',good[:-1],struct.pack('<HI',2,3)+struct.pack('<III',1,0,3)+struct.pack('<III',2,1,2)+b'abc']:
            with self.assertRaises(ValueError):parse_mix(invalid)
    def test_unpinned_data_rejected(self):
        with self.assertRaises(ValueError):decode(b'not the original cave')
if __name__=='__main__':unittest.main()
