import tempfile,unittest
from pathlib import Path
from lol2_draracle_openings import parents_and_chains,connector_side,compare_edges,obj_preview

class OpeningTests(unittest.TestCase):
    def row(self):
        r=[0]*22;r[2:6]=[65535]*4;return r
    def test_owner_chain_and_continuation(self):
        rs=[self.row() for _ in range(4)];rs[0][14]=32;rs[0][16]=1
        for i in [1,2]:rs[i][14]=128|32
        rs[1][11]=1;rs[2][11]=0
        parents,chains=parents_and_chains(rs)
        self.assertEqual(parents,{1:0,2:0});self.assertEqual(chains[0]['children'],[1,2])
    def test_orphan_rejected(self):
        r=self.row();r[14]=128
        with self.assertRaises(ValueError):parents_and_chains([r])
    def test_out_of_range_chain_rejected(self):
        r=self.row();r[14]=32;r[16]=20
        with self.assertRaises(ValueError):parents_and_chains([r])
    def test_native_connector_side(self):
        rs=[self.row() for _ in range(3)];rs[1][14]=16;rs[1][2]=0;rs[1][4]=2
        self.assertEqual(connector_side(rs,1,0),0);self.assertEqual(connector_side(rs,1,2),2)
        with self.assertRaises(ValueError):connector_side(rs,1,99)
    def test_offset_not_snapped(self):
        r=compare_edges([(0,0),(655360,0)],[(131072,65536),(393216,65536)])
        self.assertFalse(r['collinear_within_two_fixed_lsb'])
        self.assertEqual(r['max_line_distance_original_units'],1)
        self.assertAlmostEqual(r['overlap_fraction'],.4)
    def test_no_subdivision_ceiling_or_walls(self):
        r=dict(id=1,vertex_indices=[0,1,2,3],floor_corners=[0]*4,ceiling_corners=None,floor_subdivisions=[],standalone_walls=False,neighbors=[None]*4)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.obj';obj_preview(p,[(0,0),(65536,0),(65536,65536),(0,65536)],[r]);s=p.read_text()
            self.assertIn('g floor_1',s);self.assertNotIn('g ceiling_1',s);self.assertNotIn('g boundary_',s)
if __name__=='__main__':unittest.main()
