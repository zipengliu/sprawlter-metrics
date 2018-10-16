import unittest
import math
from geometric import *
from tulip import tlp
from multilevel_metrics import *


EPSILON = 1e-6


# class GeometricTest(unittest.TestCase):
#
#     def test_angle(self):
#         p1 = tlp.Vec3f(0,0,0)
#         q1 = tlp.Vec3f(1,1,0)
#         p2 = tlp.Vec3f(1,0,0)
#         q2 = tlp.Vec3f(0,1,0)
#         # case: 90 deg
#         self.assertTrue(abs(get_angle_between_line_segments(p1, q1, p2, q2) - math.pi / 2) < EPSILON)
#         p3 = tlp.Vec3f(0.5,0.5,0)
#         q3 = tlp.Vec3f(4,4,0)
#         # case: 0
#         self.assertTrue(get_angle_between_line_segments(p1, q1, p3, q3) < EPSILON)


class MathFunctionsTest(unittest.TestCase):

    def test_uniform_decay(self):
        f = get_uniform_weight_func(2)
        self.assertTrue(abs(f(0) - 0.5) < EPSILON)

    def test_linear_decay(self):
        f = get_linear_decay_func(-0.1, 4)
        self.assertTrue(abs(f(0) - 0.4) < EPSILON)
        self.assertTrue(abs(f(1) - 0.3) < EPSILON)
        self.assertTrue(abs(f(2) - 0.2) < EPSILON)
        self.assertTrue(abs(f(3) - 0.1) < EPSILON)

    def test_exponential_decay(self):
        f = get_exponential_decay_func(0.5, 4)
        self.assertTrue(abs(f(0) - 0.533) < 1E-3)
        self.assertTrue(abs(f(1) - 0.267) < 1E-3)
        self.assertTrue(abs(f(2) - 0.133) < 1E-3)
        self.assertTrue(abs(f(3) - 0.067) < 1E-3)



if __name__ == '__main__':
    unittest.main()

