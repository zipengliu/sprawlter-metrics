from tulip import tlp
from geometric import *
import math

ALPHA = 0.2
GLANCING_ANGLE_PENALTY = 5
# These coefficients for edge-edge penalty are fixed because the GLANCING_ANGLE_PENALTY (m) is fixed
ANGLE_QUAD_COEFFICIENT = 4 * (1 - ALPHA) * GLANCING_ANGLE_PENALTY / math.pi
ANGLE_LOG_COEFFICIENT = (1 - ALPHA) * GLANCING_ANGLE_PENALTY / math.log(math.pi / 2 + 1)


# penalty function of overlap area
# m is the maximum possible overlap
# Piecewise linear, slope = 1
def piecewise_linear_func(x, m):
    if x == 0:
        return 0
    elif x < (1 - ALPHA) * m:
        return x + ALPHA * m
    else:
        return m


# Linear, slope < 1
def linear_func(x, m):
    if x == 0:
        return 0
    else:
        return (1 - ALPHA) * x + ALPHA * m


# Log
def log_func(x, m):
    if x == 0:
        return 0
    else:
        # calculate the log coefficient because m can be different for different overlaps
        c = (1 - ALPHA) * m / math.log(m + 1)
        return c * math.log(x + 1) + ALPHA * m


# Penalty function for edge edge crossing
# Linear.  x the acute crossing angle is [0, PI / 2]
# Note that angle can be zero, which means part of the edges stack up / collinear
def angle_linear_func(x, m = GLANCING_ANGLE_PENALTY):
    return m * (ALPHA - 1) / (math.pi / 2) * x + m


# Quadratic function: p(x) = -kx^2 + m
def angle_quadratic_func(x, m = GLANCING_ANGLE_PENALTY):
    return -ANGLE_QUAD_COEFFICIENT * x ** 2 + m


# Log function
def angle_log_func(x, m = GLANCING_ANGLE_PENALTY):
    return ANGLE_LOG_COEFFICIENT * math.log(math.pi / 2 + 1 - x) + ALPHA * m


class MultiLevelMetrics:

    def __init__(self, graph, penalty_func_type = 'piecewise-linear', angle_penalty_func_type = 'linear'):
        self.graph = graph
        self.view_layout = graph.getLayoutProperty('viewLayout')
        self.view_size = graph.getSizeProperty('viewSize')

        if penalty_func_type == 'piecewise-linear':
            self.penalty_func = piecewise_linear_func
        elif penalty_func_type == 'linear':
            self.penalty_func = linear_func
        else:
            self.penalty_func = log_func

        if angle_penalty_func_type == 'linear':
            self.angle_penalty_func = angle_linear_func
        elif angle_penalty_func_type == 'quadratic':
            self.angle_penalty_func = angle_quadratic_func
        else:
            self.angle_penalty_func = angle_log_func

    # Get the center and radius of a node or subgraph v
    def get_bounding_circle(self, v):
        if isinstance(v, tlp.node):
            return self.view_layout[v], self.view_size[v][0] / 2
        else:
            bc = tlp.computeBoundingRadius(v)
            return bc[0], bc[0].dist(bc[1])

    # Get the penalty for overlap between a node (or a subgraph / meta-node) v and an edge e
    def get_node_edge_penalty(self, e, v):
        s = self.view_layout[self.graph.source(e)]
        t = self.view_layout[self.graph.target(e)]
        center, radius = self.get_bounding_circle(v)
        o = crossLineSegmentAndCircle(s, t, center, radius)
        if o > 0:
            max_overlap = min(math.sqrt(dist2(s, t)), radius * 2)
            p = self.penalty_func(o, max_overlap)
            print '(meta-)node {} overlaps with edge {} (overlap area: {}, penalty: {})'.format(v, e, o, p)
            return p
        else:
            return 0

    # Get the penalty for overlap between two nodes or graphs v1 and v2, given that nodes are represented as circles
    def get_node_node_penalty(self, v1, v2):
        c1, r1 = self.get_bounding_circle(v1)
        c2, r2 = self.get_bounding_circle(v2)
        # print 'getNNPenalty: ', v1, c1, r1, v2, c2, r2
        o = getCircleOverlap(c1, r1, c2, r2)
        if o > 0:
            size1 = math.pi * r1 ** 2
            size2 = math.pi * r2 ** 2
            p = self.penalty_func(o, min(size1, size2))
            print '(meta-)node {} overlaps with (meta-)node {} (overlap area: {}, penalty: {})'.format(v1, v2, o, p)
            return p
        else:
            return 0

    # Get the penalty for edge intersection
    def get_edge_edge_penalty(self, e1, e2):
        # print e1, self.graph.ends(e1), e2, self.graph.ends(e2)
        s1, t1 = [self.view_layout[x] for x in self.graph.ends(e1)]
        s2, t2 = [self.view_layout[x] for x in self.graph.ends(e2)]
        is_intersect = checkLineSegmentsIntersect(s1, t1, s2, t2)
        if is_intersect:
            a = getAngleBetweenLineSegments(s1, t1, s2, t2)
            p = self.angle_penalty_func(a)
            print 'Edge {} intersects with edge {}: angle {} (deg) penalty {}'.format(e1, e2, a * 180 / math.pi, p)
            return is_intersect, p
        else:
            return False, 0

    # Get the overall node-node penalty and count for the whole graph
    def get_graph_node_node_penalty(self):
        penalty = 0
        count = 0
                
        for n1 in self.graph.getNodes():
            # leaf node x leaf node
            for n2 in self.graph.getNodes():
                if n1.id < n2.id:        # Make sure no dupilcate pairs of nodes are considered
                    p = self.get_node_node_penalty(n1, n2)
                    count += p > 0
                    penalty += p
        
            # leaf node x subgraph
            for subGraph in self.graph.getDescendantGraphs():
                if not subGraph.isElement(n1):
                    p = self.get_node_node_penalty(n1, subGraph)
                    count += p > 0
                    penalty += p
                        
        for sub1 in self.graph.getDescendantGraphs():
            for sub2 in self.graph.getDescendantGraphs():
                if sub1.getId() < sub2.getId() and not sub2.isDescendantGraph(sub1):   # todo why not the other way?
                    p = self.get_node_node_penalty(sub1, sub2)
                    count += p > 0
                    penalty += p
                    
        return penalty, count

    def get_graph_node_edge_penalty(self):
        penalty = 0
        count = 0
        for e in self.graph.getEdges():
            s, t = self.graph.ends(e)
                    
            for node in self.graph.getNodes():
                if node != s and node != t:
                    p = self.get_node_edge_penalty(e, node)
                    count += p > 0
                    penalty += p
                    
            for subGraph in self.graph.getDescendantGraphs():
                if not subGraph.isElement(s) and not subGraph.isElement(t):
                    p = self.get_node_edge_penalty(e, subGraph)
                    count += p > 0
                    penalty += p

        return penalty, count

    def get_graph_edge_edge_penalty(self):
        penalty = 0
        count = 0
        for e1 in self.graph.getEdges():
            for e2 in self.graph.getEdges():
                if e1.id < e2.id and self.graph.source(e1) not in self.graph.ends(e2) and self.graph.target(e1) not in self.graph.ends(e2):
                    is_intersect, p = self.get_edge_edge_penalty(e1, e2)
                    count += is_intersect
                    penalty += p
        return penalty, count


if __name__ == '__main__':
    # Load the test graph
    # graph = tlp.loadGraph('test1.tlp')
    graph = tlp.loadGraph('../data/test1.tlp')
    print [x for x in graph.getNodes()]
    print [x for x in graph.getDescendantGraphs()]
    # n1 = graph.nodes()[0]
    # n2 = graph.nodes()[1]

    metrics = MultiLevelMetrics(graph, penalty_func_type='log', angle_penalty_func_type='quadratic')

    res = metrics.get_graph_node_node_penalty()
    print 'Node-node overlap: penalty: {}  count: {}'.format(res[0], res[1])
    print

    res = metrics.get_graph_node_edge_penalty()
    print 'Node-edge overlap: penalty: {}  count: {}'.format(res[0], res[1])
    print

    res = metrics.get_graph_edge_edge_penalty()
    print 'Edge-edge overlap: penalty: {}  count: {}'.format(res[0], res[1])
    print

