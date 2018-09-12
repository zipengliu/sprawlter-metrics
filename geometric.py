import math

EPSILON  = 1e-6

### All the geometric related functions
### agnostic of graph data structure


# Calculate the square of distance between two points (avoiding the slow sqrt operation)
def dist2(a, b):
    return (a.x() - b.x()) ** 2 + (a.y() - b.y()) ** 2

def dotProduct(a, b):
    return a.x() * b.x() + a.y() * b.y()


# Calculate the shortest distance from point p to a line segment ab, all points are in tlp.Vec3f 
def distFromPointToSegment(p, a, b):
    l2 = dist2(a, b)
    if l2 < EPSILON:
        # line segment ab degenerates to a single point
        return math.sqrt(dist2(p, a))
    t = max(0, min(1, dotProduct(p - a, b - a) / l2))
    projectedPoint = a + t * (b - a);
    return math.sqrt(dist2(p, projectedPoint))

# The overlap area between a line segment ab and a circle with center c and radius r
def crossLineSegmentAndCircle(a, b, c, r):
    d = distFromPointToSegment(c, a, b)
    if d - r < EPSILON:
        return math.sqrt(r ** 2 - d ** 2)
    else:
        return 0

# Calculate the area of a "half len" (pie - triangle within a circle)
# Circle radius r, triangle height d
# Equation (10) of http://mathworld.wolfram.com/Circle-CircleIntersection.html
def getHalfLenArea(r, d):
    pie = r * r * math.acos(d / r)
    triangle = d * math.sqrt(r * r - d * d)
    return pie - triangle


# Get the area of overlap between two circles. c1 and c2 are in tlp.Vec3f
# Reference: http://mathworld.wolfram.com/Circle-CircleIntersection.html
def getCircleOverlap(c1, r1, c2, r2):
    # d is the distance between c1 and c2 (centers of two circle)
    dSqr = dist2(c1, c2)
    d = math.sqrt(dSqr) 
    
    if d < abs(r1 - r2):
        # one node contains the other
        return math.pi * min(r1, r2) ** 2
    elif d < r1 + r2:
        # two nodes intersect
        d1 = (d * d - r2 * r2 + r1 * r1) / d / 2
        d2 = d - d1
        return getHalfLenArea(r1, d1) + getHalfLenArea(r2, d2)
    else:
        return 0


if __name__ == '__main__':
    # TODO Test the geometric functions
    pass
