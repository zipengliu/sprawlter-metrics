import unittest
from geometric import *
from tulip import tlp

class GeometricTest(unittest.TestCase):

    def test_intersection(self):
        p1 = tlp.Vec3f(0,0,0)
        q1 = tlp.Vec3f(1,1,0)
        p2 = tlp.Vec3f(1,0,0)
        q2 = tlp.Vec3f(0,1,0)
        self.assertTrue(checkLineSegmentsIntersect(p1, q1, p2, q2))
        self.assertFalse(checkLineSegmentsIntersect(p1, p2, q1, q2))
        p3 = tlp.Vec3f(1,1,0)
        q3 = tlp.Vec3f(4,4,0)
        self.assertTrue(checkLineSegmentsIntersect(p1, q1, p3, q3))
        p4 = tlp.Vec3f(0.5,0.5,0)
        self.assertTrue(checkLineSegmentsIntersect(p1, q1, p4, q3))
        self.assertFalse(checkLineSegmentsIntersect(p1, p4, p3, q3))
        p5 = tlp.Vec3f(-1, 10, 0)
        self.assertFalse(checkLineSegmentsIntersect(p1, q1, p5, q2))

    def test_angle(self):
        pass

if __name__ == '__main__':
    unittest.main()

