import unittest
import math
from geometric import *
from tulip import tlp

EPSILON = 1e-6

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
        p1 = tlp.Vec3f(0,0,0)
        q1 = tlp.Vec3f(1,1,0)
        p2 = tlp.Vec3f(1,0,0)
        q2 = tlp.Vec3f(0,1,0)
        # case: 90 deg
        self.assertTrue(abs(getAngleBetweenLineSegments(p1, q1, p2, q2) - math.pi / 2) < EPSILON)
        p3 = tlp.Vec3f(0.5,0.5,0)
        q3 = tlp.Vec3f(4,4,0)
        # case: 0
        self.assertTrue(getAngleBetweenLineSegments(p1, q1, p3, q3) < EPSILON)

    def test_circle_overlap(self):
        c1 = tlp.Vec3f(333.75, 272.75, 0)
        r1 = 95.75
        c2 = tlp.Vec3f(198.25, 202.25, 0)
        r2 = 34.25
        self.assertEqual(getCircleOverlap(c1, r1, c2, r2), 0)
        c2 = tlp.Vec3f(241.25, 234.25, 0)
        r2 = 34.25
        o = getCircleOverlap(c1, r1, c2, r2)
        self.assertTrue(o > 0 and math.pi * r2 ** 2 - o > 0)
        c2 = tlp.Vec3f(336.47674, 260.5, 0)
        r2 = 50
        o = getCircleOverlap(c1, r1, c2, r2)
        self.assertTrue(abs(math.pi * r2 ** 2 - o) < EPSILON)


    def test_line_segment_circle_crossing(self):
        p = tlp.Vec3f(157.76, 197.55, 0)
        q = tlp.Vec3f(423.80, 144.83, 0)
        c = tlp.Vec3f(333.75, 272.75, 0)
        r = 95.75
        self.assertEqual(crossLineSegmentAndCircle(p, q, c, r), 0)
        p = tlp.Vec3f(153.5, 211.0547, 0)
        q = tlp.Vec3f(419.53906, 158.32812, 0)
        self.assertTrue(crossLineSegmentAndCircle(p, q, c, r) > 0)
        p = tlp.Vec3f(89.5, 380.35156, 0)
        q = tlp.Vec3f(219.1328, 324, 0)
        self.assertEqual(crossLineSegmentAndCircle(p, q, c, r), 0)



if __name__ == '__main__':
    unittest.main()

