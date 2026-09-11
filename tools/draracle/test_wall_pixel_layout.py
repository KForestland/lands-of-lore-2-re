import unittest
from extract_wall_texture_review import column_major_to_rows
class WallLayoutTests(unittest.TestCase):
 def test_rectangular_columns(self):
  self.assertEqual(column_major_to_rows(bytes([1,4,2,5,3,6]),3,2),bytes([1,2,3,4,5,6]))
 def test_square_transpose(self):
  self.assertEqual(column_major_to_rows(bytes([1,3,2,4]),2,2),bytes([1,2,3,4]))
