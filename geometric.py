import math

EPSILON  = 1e-6

### All the geometric related functions
### agnostic of graph data structure


# Calculate the square of distance between two points (avoiding the slow sqrt operation)
def dist2(a, b):
    return (a.x() - b.x()) ** 2 + (a.y() - b.y()) ** 2

def dist(a, b):
    return math.sqrt(dist2(a, b))

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

# Get the angle of two line segments given they intersect
def getAngleBetweenLineSegments(a, b, c, d):
    vec1 = b - a
    vec2 = d - c
    cosVal = dotProduct(vec1, vec2) / (dist(a, b) * dist(c, d))
    return math.acos(abs(cosVal))


# Given three colinear points p, q, r, the function checks if 
# point q lies on line segment qr
def onSegment(p, q, r):
    return q.x() <= max(p.x(), r.x()) and q.x() >= min(p.x(), r.x()) \
            and q.y() <= max(p.y(), r.y()) and q.y() >= min(p.y(), r.y())

# To find orientation of ordered triplet (p, q, r). 
# The function returns following values 
# 0 --> p, q and r are colinear 
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
def checkLineSegmentsIntersect(p1, q1, p2, q2):
    o1 = orientation(p1, q1, p2) 
    o2 = orientation(p1, q1, q2) 
    o3 = orientation(p2, q2, p1) 
    o4 = orientation(p2, q2, q1) 
  
    # General case 
    if o1 != o2 and o3 != o4:
        return True
  
    # Special Cases 
    # p1, q1 and p2 are colinear and p2 lies on segment p1q1 
    if o1 == 0 and onSegment(p1, p2, q1):
        return True
  
    # p1, q1 and q2 are colinear and q2 lies on segment p1q1 
    if o2 == 0 and onSegment(p1, q2, q1):
        return True
  
    # p2, q2 and p1 are colinear and p1 lies on segment p2q2 
    if o3 == 0 and onSegment(p2, p1, q2):
        return True
  
    # p2, q2 and q1 are colinear and q1 lies on segment p2q2 
    if o4 == 0 and onSegment(p2, q1, q2):
        return True
  
    return False 
    

if __name__ == '__main__':
    # TODO Test the geometric functions
    pass
