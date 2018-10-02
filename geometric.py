from __future__ import division
import math

EPSILON  = 1e-6

# All the geometric related functions
# agnostic of graph data structure


# Calculate the square of distance between two points (avoiding the slow sqrt operation)
def dist2(a, b):
    return (a.x() - b.x()) ** 2 + (a.y() - b.y()) ** 2


def dist(a, b):
    return math.sqrt(dist2(a, b))


def dot_product(a, b):
    return a.x() * b.x() + a.y() * b.y()


# Calculate the shortest distance from point p to a line segment ab, all points are in tlp.Vec3f 
# def dist_from_point_to_segment(p, a, b):
#     l2 = dist2(a, b)
#     if l2 < EPSILON:
#         # line segment ab degenerates to a single point
#         return dist(p, a)
#     t = max(0, min(1, dot_product(p - a, b - a) / l2))
#     projected_point = a + t * (b - a)
#     return dist(p, projected_point)


# Solve the quadratic function ax^2 + bx + c = 0
# Return the two x values if solvable, otherwise return None
def solve_quadratic_function(a, b, c):
    p = b ** 2 - 4 * a * c
    if p >= EPSILON:
        return (-b - math.sqrt(p)) / a / 2, (-b + math.sqrt(p)) / a / 2
    else:
        return None, None


# The overlap area between a line segment ab and a circle with center c and radius r
def cross_line_segment_and_circle(a, b, c, r):
    # d = dist_from_point_to_segment(c, a, b)
    # if d - r < EPSILON:
    #     dist_a2 = dist2(c, a)
    #     dist_b2 = dist2(c, b)
    #     r2 = r ** 2
    #     if dist_a2 - r2 > EPSILON and dist_b2 - r2 > EPSILON:
    #         # case 1: a, b are both outside of the circle
    #         return 2 * math.sqrt(r2 - d ** 2)
    #     elif dist_a2 - r2 < EPSILON and dist_b2 - r2 < EPSILON:
    #         # case 2: a, b are both inside the circle
    #         return dist(a, b)
    #     else:
    #         # case 3: one of a, b is inside circle and the other outside
    #         pass
    # else:
    #     return 0

    k1 = a.x() - b.x()
    k2 = a.y() - b.y()
    b1 = b.x() - c.x()
    b2 = b.y() - c.y()
    # t0 <= t <= t1
    t0, t1 = solve_quadratic_function(k1 ** 2 + k2 ** 2, 2 * (k1 * b1 + k2 * b2), b1 ** 2 + b2 ** 2 - r ** 2)
    if t0 is None:
        return 0
    # t must be within [0, 1]
    t0 = max(0, t0)
    t1 = min(1, t1)
    if t1 - t0 >= EPSILON:
        return (t1 - t0) * dist(a, b)
    else:
        return 0


# Calculate the area of a "half len" (pie - triangle within a circle)
# Circle radius r, triangle height d
# Equation (10) of http://mathworld.wolfram.com/Circle-CircleIntersection.html
def get_half_len_area(r, d):
    pie = r * r * math.acos(d / r)
    triangle = d * math.sqrt(r * r - d * d)
    return pie - triangle


# Get the area of overlap between two circles. c1 and c2 are in tlp.Vec3f
# Reference: http://mathworld.wolfram.com/Circle-CircleIntersection.html
def get_circle_overlap(c1, r1, c2, r2):
    # d is the distance between c1 and c2 (centers of two circle)
    d_sqr = dist2(c1, c2)
    d = math.sqrt(d_sqr)
    
    if d - abs(r1 - r2) < EPSILON:
        # one node contains the other
        return math.pi * min(r1, r2) ** 2
    elif d - (r1 + r2) < EPSILON:
        # two nodes intersect
        d1 = (d * d - r2 * r2 + r1 * r1) / d / 2
        d2 = d - d1
        return get_half_len_area(r1, d1) + get_half_len_area(r2, d2)
    else:
        return 0


# Get the angle of two line segments given they intersect
def get_angle_between_line_segments(a, b, c, d):
    vec1 = b - a
    vec2 = d - c
    cos_val = abs(dot_product(vec1, vec2) / (dist(a, b) * dist(c, d)))
    # Clamp cos_val to [0,1] (this happens b/c floating operation error)
    cos_val = min(1, max(0, cos_val))
    return math.acos(cos_val)


# Given three collinear points p, q, r, the function checks if
# point q lies on line segment qr
def is_on_segment(p, q, r):
    return min(p.x(), r.x()) <= q.x() <= max(p.x(), r.x()) and min(p.y(), r.y()) <= q.y() <= max(p.y(), r.y())


# To find orientation of ordered triplet (p, q, r). 
# The function returns following values 
# 0 --> p, q and r are collinear
# 1 --> Clockwise 
# 2 --> Counterclockwise 
def orientation(p, q, r):
    val = (q.y() - p.y()) * (r.x() - q.x()) - (q.x() - p.x()) * (r.y() - q.y())
  
    if val == 0:
        return 0  
    elif val > 0:
        return 1
    else:
        return 2


# Check if two line segments intersect
# Reference: https://www.geeksforgeeks.org/check-if-two-given-line-segments-intersect/
def check_line_segments_intersect(p1, q1, p2, q2):
    o1 = orientation(p1, q1, p2) 
    o2 = orientation(p1, q1, q2) 
    o3 = orientation(p2, q2, p1) 
    o4 = orientation(p2, q2, q1) 
  
    # General case 
    if o1 != o2 and o3 != o4:
        return True
  
    # Special Cases 
    # p1, q1 and p2 are collinear and p2 lies on segment p1q1
    if o1 == 0 and is_on_segment(p1, p2, q1):
        return True
  
    # p1, q1 and q2 are collinear and q2 lies on segment p1q1
    if o2 == 0 and is_on_segment(p1, q2, q1):
        return True
  
    # p2, q2 and p1 are collinear and p1 lies on segment p2q2
    if o3 == 0 and is_on_segment(p2, p1, q2):
        return True
  
    # p2, q2 and q1 are collinear and q1 lies on segment p2q2
    if o4 == 0 and is_on_segment(p2, q1, q2):
        return True
  
    return False 
    

