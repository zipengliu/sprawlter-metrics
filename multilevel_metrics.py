from tulip import tlp
from geometric import *
import math

LOG_BASE = 2
ALPHA = 0.2


# penalty function of overlap area
# m is the maximum possible overlap
# Linear, slope = 1
def penaltyFunc(x, m):
    if x == 0:
        return 0
    elif x < (1 - ALPHA) * m:
        return x + ALPHA * m
    else:
        return m

# Linear, slope < 1
# def penaltyFunc(x, m):
#     if x == 0:
#         return 0
#     else:
#         return (1 - ALPHA) * x + ALPHA * m


# Log
# def penaltyFunc(x, m):
#     if x == 0:
#         return 0
#     else:
#         return math.log(x + 1, LOG_BASE) + ALPHA * m


# Penalty function for edge edge crossing
# Linear.  x the acute crossing angle is [0, PI / 2]
# Note that angle can be zero, which means part of the edges stack up
def anglePenaltyFunc(x, m):
    return m * (ALPHA - 1) / (math.pi / 2) * x + m


class MultiLevelMetrics:

    def __init__(self, graph):
        self.graph = graph
        self.viewLayout = graph.getLayoutProperty('viewLayout')
        self.viewSize = graph.getSizeProperty('viewSize')

    # Get the center and radius of a node or subgraph v
    def getNodeCircle(self, v):
        if isinstance(v, tlp.node):
            return self.viewLayout[v], self.viewSize[v][0] / 2
        else:
            bc = tlp.computeBoundingRadius(v)
            return bc[0], bc[0].dist(bc[1])

    # Get the penalty for overlap between a node (or a subgraph / meta-node) v and an edge e
    def getNodeEdgePenalty(self, e, v):
        s = self.viewLayout[self.graph.source(e)]
        t = self.viewLayout[self.graph.target(e)]
        center, radius = self.getNodeCircle(v)
        o = crossLineSegmentAndCircle(s, t, center, radius)
        if o > 0:
            max_overlap = min(math.sqrt(dist2(s, t)), radius * 2)
            p = penaltyFunc(o, max_overlap)
            print '(meta-)node {} overlaps with edge {} (overlap area: {}, penalty: {})'.format(v, e, o, p)
            return p
        else:
            return 0

    # Get the penalty for overlap between two nodes or graphs v1 and v2, given that nodes are represented as circles
    def getNodeNodePenalty(self, v1, v2):
        c1, r1 = self.getNodeCircle(v1)
        c2, r2 = self.getNodeCircle(v2)
        # print 'getNNPenalty: ', v1, c1, r1, v2, c2, r2
        o = getCircleOverlap(c1, r1, c2, r2)
        if o > 0:
            size1 = math.pi * r1 ** 2
            size2 = math.pi * r2 ** 2
            p = penaltyFunc(o, min(size1, size2))
            print '(meta-)node {} overlaps with (meta-)node {} (overlap area: {}, penalty: {})'.format(v1, v2, o, p)
            return p
        else:
            return 0

    # Get the penalty for edge intersection
    def getEdgeEdgePenalty(self, e1, e2):
        # print e1, self.graph.ends(e1), e2, self.graph.ends(e2)
        s1, t1 = [self.viewLayout[x] for x in self.graph.ends(e1)]
        s2, t2 = [self.viewLayout[x] for x in self.graph.ends(e2)]
        isIntersect = checkLineSegmentsIntersect(s1, t1, s2, t2)
        if isIntersect:
            a = getAngleBetweenLineSegments(s1, t1, s2, t2)
            p = anglePenaltyFunc(a, 2)         # TODO the max penalty should be a parameter somewhere
            print 'Edge {} intersects with edge {}: angle {} (deg) penalty {}'.format(e1, e2, a * 180 / math.pi, p)
            return isIntersect, p
        else:
            return False, 0

    # Get the overall node-node penalty and count for the whole graph
    def getGraphNodeNodePenalty(self):
        penalty = 0
        count = 0
                
        for n1 in self.graph.getNodes():
            # leaf node x leaf node
            for n2 in self.graph.getNodes():
                if n1.id < n2.id:        # Make sure no dupilcate pairs of nodes are considered
                    p = self.getNodeNodePenalty(n1, n2)
                    count += p > 0
                    penalty += p
        
            # leaf node x subgraph
            for subGraph in self.graph.getDescendantGraphs():
                if not subGraph.isElement(n1):
                    p = self.getNodeNodePenalty(n1, subGraph)
                    count += p > 0
                    penalty += p
                        
        for sub1 in self.graph.getDescendantGraphs():
            for sub2 in self.graph.getDescendantGraphs():
                if sub1.getId() < sub2.getId() and not sub2.isDescendantGraph(sub1):   # todo why not the other way?
                    p = self.getNodeNodePenalty(sub1, sub2)
                    count += p > 0
                    penalty += p
                    
        return penalty, count

    def getGraphNodeEdgePenalty(self):
        penalty = 0
        count = 0
        for e in self.graph.getEdges():
            s, t = self.graph.ends(e)
                    
            for node in self.graph.getNodes():
                if node != s and node != t:
                    p = self.getNodeEdgePenalty(e, node)
                    count += p > 0
                    penalty += p
                    
            for subGraph in self.graph.getDescendantGraphs():
                if not subGraph.isElement(s) and not subGraph.isElement(t):
                    p = self.getNodeEdgePenalty(e, subGraph)
                    count += p > 0
                    penalty += p

        return penalty, count

    def getGraphEdgeEdgePenalty(self):
        penalty = 0
        count = 0
        for e1 in self.graph.getEdges():
            for e2 in self.graph.getEdges():
                if e1.id < e2.id and self.graph.source(e1) not in self.graph.ends(e2) and self.graph.target(e1) not in self.graph.ends(e2):
                    isIntersect, p = self.getEdgeEdgePenalty(e1, e2)
                    count += isIntersect
                    penalty += p
        return penalty, count


if __name__ == '__main__':
    # Load the test graph
    # graph = tlp.loadGraph('test1.tlp')
    graph = tlp.loadGraph('../data/four-clusters1/four-clusters1-edge-edge-overlap1.tlp')
    print [x for x in graph.getNodes()]
    print [x for x in graph.getDescendantGraphs()]
    # n1 = graph.nodes()[0]
    # n2 = graph.nodes()[1]

    metrics = MultiLevelMetrics(graph)

    res = metrics.getGraphNodeNodePenalty()
    print 'Node-node overlap: penalty: {}  count: {}'.format(res[0], res[1])

    res = metrics.getGraphNodeEdgePenalty()
    print 'Node-edge overlap: penalty: {}  count: {}'.format(res[0], res[1])

    res = metrics.getGraphEdgeEdgePenalty()
    print 'Edge-edge overlap: penalty: {}  count: {}'.format(res[0], res[1])

