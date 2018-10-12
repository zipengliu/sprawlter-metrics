from __future__ import division
from tulip import tlp
from geometric import *
import math

ALPHA = 0.2
GLANCING_ANGLE_PENALTY = 5
# These coefficients for edge-edge penalty are fixed because the GLANCING_ANGLE_PENALTY (m) is fixed
ANGLE_QUAD_COEFFICIENT = 4 * (1 - ALPHA) * GLANCING_ANGLE_PENALTY / math.pi
ANGLE_LOG_COEFFICIENT = (1 - ALPHA) * GLANCING_ANGLE_PENALTY / math.log(math.pi / 2 + 1)

LINEAR_DECAY_RATE = -0.1
EXPONENTIAL_DECAY_RATE = 0.5


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


def get_uniform_weight_func(h):
    return lambda i: 1 / h


def get_exponential_decay_func(a, h):
    coefficient = (1 - a) / (1 - a ** h)
    return lambda i: coefficient * a ** i


def get_linear_decay_func(k, h):
    b = 1 / h - (h - 1) / 2 * k
    return lambda i: k * i + b


class MultiLevelMetrics:

    def __init__(self, graph, penalty_func_type = 'piecewise-linear', angle_penalty_func_type = 'linear',
                 hierarchical_weight_func_type = 'uniform', debug=False):
        self.graph = graph
        self.debug = debug
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

        # Get the height of the node hierarchy
        self.height = 0
        self.subgraph_levels = {}
        self.get_hierarchy_height()
        if hierarchical_weight_func_type == 'uniform':
            self.weight_func = get_uniform_weight_func(self.height)
        elif hierarchical_weight_func_type == 'linear':
            self.weight_func = get_linear_decay_func(LINEAR_DECAY_RATE, self.height)
        else:
            self.weight_func = get_exponential_decay_func(EXPONENTIAL_DECAY_RATE, self.height)

    # This is the same level counting method in the Bourqui multi-level force layout paper.
    def get_hierarchy_height(self):
        def dfs(g, cur_height):
            self.subgraph_levels[g.getId()] = cur_height
            self.height = max(self.height, cur_height + 1)
            for s in g.getSubGraphs():
                dfs(s, cur_height + 1)
        dfs(self.graph, 0)

    # For detailed penalty and count information
    # Each cell(i,j) corresponds to the penalty / count of items at level i and level j
    def get_initial_count_table(self):
        # There should be height + 1 rows and columns
        n = self.height + 1
        return [[0 for j in range(n)] for i in range(n)],\
               [[0 for j in range(n)] for i in range(n)]

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
        o = cross_line_segment_and_circle(s, t, center, radius)
        if o > 0:
            max_overlap = min(dist(s, t), radius * 2)
            p = self.penalty_func(o, max_overlap)
            if self.debug:
                print '(meta-)node {} overlaps with edge {} (overlap area: {}, penalty: {})'.format(v, e, o, p)
            return p
        else:
            return 0

    # Get the penalty for overlap between two nodes or graphs v1 and v2, given that nodes are represented as circles
    def get_node_node_penalty(self, v1, v2):
        c1, r1 = self.get_bounding_circle(v1)
        c2, r2 = self.get_bounding_circle(v2)
        # print 'getNNPenalty: ', v1, c1, r1, v2, c2, r2
        o = get_circle_overlap(c1, r1, c2, r2)
        if o > 0:
            size1 = math.pi * r1 ** 2
            size2 = math.pi * r2 ** 2
            p = self.penalty_func(o, min(size1, size2))
            if self.debug:
                print '(meta-)node {} overlaps with (meta-)node {} (overlap area: {}, penalty: {})'.format(v1, v2, o, p)
            return p
        else:
            return 0

    # Get the penalty for edge intersection
    def get_edge_edge_penalty(self, e1, e2):
        # print e1, self.graph.ends(e1), e2, self.graph.ends(e2)
        s1, t1 = [self.view_layout[x] for x in self.graph.ends(e1)]
        s2, t2 = [self.view_layout[x] for x in self.graph.ends(e2)]
        is_intersect = check_line_segments_intersect(s1, t1, s2, t2)
        if is_intersect and dist2(s1, t1) > EPSILON and dist2(s2, t2) > EPSILON:
            a = get_angle_between_line_segments(s1, t1, s2, t2)
            p = self.angle_penalty_func(a)
            if self.debug:
                print 'Edge {} intersects with edge {}: angle {} (deg) penalty {}'.format(e1, e2, a * 180 / math.pi, p)
            return is_intersect, p
        else:
            return False, 0

    # Get the overall node-node penalty and count for the whole graph
    def get_graph_node_node_penalty(self):
        penalty = 0
        count = 0
        penalty_lvl, count_lvl = self.get_initial_count_table()

        for n1 in self.graph.getNodes():
            # leaf node x leaf node
            for n2 in self.graph.getNodes():
                if n1.id < n2.id:        # Make sure no duplicate pairs of nodes are considered
                    p = self.get_node_node_penalty(n1, n2)
                    if p > 0:
                        count += 1
                        penalty += self.weight_func(self.height - 1) * p
                        count_lvl[-1][-1] += 1
                        penalty_lvl[-1][-1] += p

            # leaf node x subgraph
            for subGraph in self.graph.getDescendantGraphs():
                if not subGraph.isElement(n1):
                    p = self.get_node_node_penalty(n1, subGraph)
                    if p > 0:
                        count += 1
                        lvl = self.subgraph_levels[subGraph.getId()]
                        penalty += self.weight_func(lvl) * p
                        count_lvl[lvl][-1] += 1
                        penalty_lvl[lvl][-1] += p

        for sub1 in self.graph.getDescendantGraphs():
            for sub2 in self.graph.getDescendantGraphs():
                if sub1.getId() < sub2.getId() and not sub2.isDescendantGraph(sub1) and not sub1.isDescendantGraph(sub2):
                    p = self.get_node_node_penalty(sub1, sub2)
                    if p > 0:
                        count += p > 0
                        # Assuming weight function takes the higher one in the hierarchy
                        lvl1 = self.subgraph_levels[sub1.getId()]
                        lvl2 = self.subgraph_levels[sub2.getId()]
                        min_lvl = min(lvl1, lvl2)
                        max_lvl = max(lvl1, lvl2)
                        penalty += self.weight_func(min_lvl) * p
                        # Fill the upper-right triangle of the counting table
                        count_lvl[min_lvl][max_lvl] += 1
                        penalty_lvl[min_lvl][max_lvl] += p

        return {'total_penalty': penalty, 'penalty_by_level': penalty_lvl,
                'total_count': count, 'count_by_level': count_lvl}

    def get_graph_node_edge_penalty(self):
        penalty = 0
        count = 0
        for e in self.graph.getEdges():
            s, t = self.graph.ends(e)
                    
            for node in self.graph.getNodes():
                if node != s and node != t:
                    p = self.get_node_edge_penalty(e, node)
                    count += p > 0
                    penalty += self.weight_func(self.height - 1) * p
                    
            for subGraph in self.graph.getDescendantGraphs():
                if not subGraph.isElement(s) and not subGraph.isElement(t):
                    p = self.get_node_edge_penalty(e, subGraph)
                    count += p > 0
                    penalty += self.weight_func(self.subgraph_levels[subGraph.getId()]) * p

        return penalty, count

    def get_graph_edge_edge_penalty(self):
        penalty = 0
        count = 0
        for e1 in self.graph.getEdges():
            for e2 in self.graph.getEdges():
                if e1.id < e2.id:
                    ends1 = self.graph.ends(e1)
                    ends2 = self.graph.ends(e2)
                    if ends1[0] not in ends2 and ends1[1] not in ends2 and ends1[0] != ends1[1] and ends2[0] != ends2[1]:
                        is_intersect, p = self.get_edge_edge_penalty(e1, e2)
                        count += is_intersect
                        penalty += p
        return penalty, count


# Print out the penalty and count by level
def print_by_level(p, c):
    n = len(p[0])
    header_format = '\t{:5}' + '{:10}' * (n - 1)
    row_format = '\t{:5}' + '{:10.2f}' * (n - 1)
    print '\tPenalty by level (max level corresponds to leaf nodes, level 0 to the whole graph):'
    print header_format.format('level', *range(1, n))
    for i in range(1, n):
        print row_format.format(i, *p[i][1:])
    print

    print '\tCount by level:'
    row_format = '\t{:5}' + '{:10}' * (n - 1)
    print header_format.format('level', *range(1, n))
    for i in range(1, n):
        print row_format.format(i, *c[i][1:])
    print


# Handy function to get a pretty print out of results
def run_and_print(filename, **metrics_args):
    graph = tlp.loadGraph(filename)
    metrics = MultiLevelMetrics(graph, **metrics_args)
    print '===== ', filename, ' ====='
    print '#nodes: {}  #edges: {}  height of node hiearachy: {}'.format(graph.numberOfNodes(), graph.numberOfEdges(), metrics.height)
    print

    nn = metrics.get_graph_node_node_penalty()
    print 'Node-node penalty: {:10.2f}   count: {:7}'.format(nn['total_penalty'], nn['total_count'])
    print_by_level(nn['penalty_by_level'], nn['count_by_level'])

    ne = metrics.get_graph_node_edge_penalty()
    print 'Node-edge penalty: {:10.2f}   count: {:7}'.format(ne[0], ne[1])

    ee = metrics.get_graph_edge_edge_penalty()
    print 'Edge-edge penalty: {:10.2f}   count: {:7}'.format(ee[0], ee[1])
    print '===== END ====='
    print


if __name__ == '__main__':
    # Load the test graph
    # graph = tlp.loadGraph('test1.tlp')
    # graph = tlp.loadGraph('../data/test1.tlp')
    # print [x for x in graph.getNodes()]
    # print [x for x in graph.getDescendantGraphs()]
    # # n1 = graph.nodes()[0]
    # # n2 = graph.nodes()[1]
    #
    # metrics = MultiLevelMetrics(graph, penalty_func_type='log', angle_penalty_func_type='quadratic',
    #                             hierarchical_weight_func_type='exponential', debug=False)
    #
    # res = metrics.get_graph_node_node_penalty()
    # print 'Node-node overlap: penalty: {}  count: {}'.format(res['total_penalty'], res['total_count'])
    # print res['penalty_by_level']
    # print res['count_by_level']
    # print
    #
    # res = metrics.get_graph_node_edge_penalty()
    # print 'Node-edge overlap: penalty: {}  count: {}'.format(res[0], res[1])
    # print
    #
    # res = metrics.get_graph_edge_edge_penalty()
    # print 'Edge-edge overlap: penalty: {}  count: {}'.format(res[0], res[1])
    # print

    run_and_print('../data/test1.tlp')
