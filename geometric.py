from __future__ import division
import math

EPSILON  = 1e-6

# Geometric functions not provided by Shapely


# Get the angle of two line segments given they intersect
def get_angle_between_line_segments(l1, l2):
    c1 = l1.coords
    c2 = l2.coords
    vec1 = (c1[1][0] - c1[0][0], c1[1][1] - c1[0][1])
    vec2 = (c2[1][0] - c2[0][0], c2[1][1] - c2[0][1])
    cos_val = abs(vec1[0] * vec2[0] + vec1[1] * vec2[1]) / (l1.length * l2.length)
    # Clamp cos_val to [0,1] (this happens b/c floating operation error)
    cos_val = min(1, max(0, cos_val))
    return math.acos(cos_val)


