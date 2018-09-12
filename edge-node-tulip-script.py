from tulip import tlp
import math

EPSILON = 1e-6

def main(graph):
  
  viewLayout = graph.getLayoutProperty('viewLayout')
  viewSize = graph.getSizeProperty('viewSize')
  

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
      return math.sqrt(r ** 2 - d ** 2) if r - d > EPSILON else 0
    
  
  def getNodeOverlap(e, v):
      s = viewLayout[graph.source(e)]
      t = viewLayout[graph.target(e)]
      return crossLineSegmentAndCircle(s, t, viewLayout[v], viewSize[v][0] / 2)
  
  def getSubGraphOverlap(e, g):
      s = viewLayout[graph.source(e)]
      t = viewLayout[graph.target(e)]
      bc = tlp.computeBoundingRadius(g)
      return crossLineSegmentAndCircle(s, t, bc[0], bc[0].dist(bc[1]))
 
  def getSubGraphPenalty(e, g):
      # print '\t',e, g
      sum = getSubGraphOverlap(e, g)
      for s in g.getDescendantGraphs():
          sum += getSubGraphOverlap(e, s)
      for n in g.getNodes():
          sum += getNodeOverlap(e, n)
      return sum

  def getGraphPenalty(g):
      penalty = 0
      for e in graph.getEdges():
          s, t = graph.ends(e)
          p = 0
          
          for subGraph in graph.getDescendantGraphs():
              if not subGraph.isElement(s) and not subGraph.isElement(t):
                  p += getSubGraphPenalty(e, subGraph)
          
          for node in graph.getNodes():
              if node != s and node != t:
                  p += getNodeOverlap(e, node)
                  
          print 'penalty for edge {} is {}'.format(e, p)
          penalty += p
      return penalty
  
  print getGraphPenalty(graph)
  
