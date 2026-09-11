import unittest
from build_creature_group_review import group_frames

class CreatureGroupTests(unittest.TestCase):
    def descriptors(self):
        return {10:(100,8,8,0x1246,2,1,77),11:(101,8,8,0x1246,258,1,77)}

    def test_count_and_index_are_separate_bytes(self):
        self.assertEqual(group_frames(self.descriptors())[0]['frames'],[10,11])

    def test_missing_variant_rejected(self):
        rows=self.descriptors();del rows[11]
        with self.assertRaises(ValueError):group_frames(rows)

    def test_wrong_group_hash_rejected(self):
        rows=self.descriptors();rows[11]=(*rows[11][:6],78)
        with self.assertRaises(ValueError):group_frames(rows)
