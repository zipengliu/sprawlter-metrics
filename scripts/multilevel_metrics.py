from __future__ import division
from tulip import tlp
from shapely.geometry import *
from geometric import *
from pprint import pprint
import math
import json, os

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
        self.debug = debug

        # Retrieve nodes and edges from graph and construct Shapely geometries
        view_layout = graph.getLayoutProperty('viewLayout')
        view_size = graph.getSizeProperty('viewSize')
        # THe node id should equal to the index in this array  TODO: verify whether this is true
        self.leaf_nodes = [{'id': n.id, 'parent_metanode': None,        # fulfill later
                            'geometry': Point(view_layout[n].x(), view_layout[n].y()).buffer(view_size[n][0] / 2.0, cap_style=CAP_STYLE.round),
                            'diameter': view_size[n][0]}
                           for n in graph.nodes()]
        # THe edge id should equal to the index in this array  TODO: verify whether this is true
        self.edges = []
        for e in graph.getEdges():
            src, tgt = graph.ends(e)
            self.edges.append({'id': e.id,
                               'ends': (src.id, tgt.id),
                               'geometry': LineString([(view_layout[src].x(), view_layout[src].y()),
                                                       (view_layout[tgt].x(), view_layout[tgt].y())])})

        self.height = 0
        self.metanodes = {}
        self.metaedges = {}
        self.root = graph.getId()
        self.retrieve_hierarchy(graph)

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
        if hierarchical_weight_func_type == 'uniform':
            self.weight_func = get_uniform_weight_func(self.height)
        elif hierarchical_weight_func_type == 'linear':
            self.weight_func = get_linear_decay_func(LINEAR_DECAY_RATE, self.height)
        else:
            self.weight_func = get_exponential_decay_func(EXPONENTIAL_DECAY_RATE, self.height)

    # Construct a simple node (graph) hierarchy data structure from the tulip graph and count levels
    # This is the same level counting method in the Bourqui multi-level force layout paper.
    def retrieve_hierarchy(self, graph):
        def dfs(g, cur_height):
            node = {'id': g.getId(),
                    'geometry': None,
                    'diameter': 0,
                    'desc_metanodes': {},
                    'parent_metanode': None,
                    'leaf_nodes': {},
                    'level': cur_height}

            # For finding whether a node is in a subgraph
            for leaf in g.getNodes():
                node['leaf_nodes'][leaf.id] = True
            # For finding whether two meta-nodes are on the same path of the node hierarchy
            for s in g.getDescendantGraphs():
                node['desc_metanodes'][s.getId()] = True

            self.height = max(self.height, cur_height + 1)
            for s in g.getSubGraphs():
                dfs(s, cur_height + 1)
                self.metanodes[s.getId()]['parent_metanode'] = g.getId()

            # Add the field parent_metanode to the leaf node
            for leaf in g.getNodes():
                tmp = self.leaf_nodes[leaf.id]
                if tmp['parent_metanode'] is None:
                    tmp['parent_metanode'] = g.getId()

            # Compute convex hull of this sub-graph in post-order
            if g.numberOfSubGraphs() == 0:
                # compute a convex hull of its leaf nodes
                coords = tlp.computeConvexHull(g)
                node['geometry'] = Polygon([(c.x(), c.y()) for c in coords])
            else:
                # union the convex hull of its sub-graphs
                node['geometry'] = MultiPolygon([self.metanodes[s.getId()]['geometry'] for s in g.getSubGraphs()]).convex_hull

            # Note that we don't compute the real diameter for a polygon, but instead, only use the diagonal of
            # the axis aligned bounding box to approximate the diameter, which is cheap to compute
            bbox = node['geometry'].bounds
            node['diameter'] = Point(bbox[0], bbox[1]).distance(Point(bbox[2], bbox[3]))

            self.metanodes[g.getId()] = node

        # Get the metanodes
        dfs(graph, 0)
        if self.debug:
            pprint(self.metanodes)

        # iterate all pairs of metanodes that contains the two leaf nodes of leaf edge e
        def metanodes_pair_iter(e):
            src, tgt = graph.ends(e)
            p1 = self.leaf_nodes[src.id]['parent_metanode']
            p2 = self.leaf_nodes[tgt.id]['parent_metanode']
            if self.debug:
                assert p1 is not None
                assert p2 is not None

            metaedge_req = lambda i, j: i != self.root and j != self.root and i != j and \
                                        j not in self.metanodes[i]['desc_metanodes'] and \
                                        i not in self.metanodes[j]['desc_metanodes']
            # Traverse from the leaf node upward all the way to root graph
            while p1 != self.root:
                p2 = self.leaf_nodes[tgt.id]['parent_metanode']
                while metaedge_req(p1, p2):
                    yield min(p1, p2), max(p1, p2)
                    p2 = self.metanodes[p2]['parent_metanode']
                p1 = self.metanodes[p1]['parent_metanode']

        # Get the metaedges, which are edges connecting two metanodes
        edge_id_format = '{}-{}'
        for e in graph.getEdges():
            for p1, p2 in metanodes_pair_iter(e):
                edge_id = edge_id_format.format(p1, p2)
                if edge_id not in self.metaedges:
                    self.metaedges[edge_id] = {'id': edge_id, 'ends': [p1, p2],
                                               'level': min(self.metanodes[p1]['level'], self.metanodes[p2]['level']),
                                               'leaf_edges': [e.id],
                                               'geometry': None}
                else:
                    self.metaedges[edge_id]['leaf_edges'].append(e.id)
        for _, me in self.metaedges.iteritems():
            me['geometry'] = MultiLineString([self.edges[eid]['geometry'] for eid in me['leaf_edges']]).convex_hull

        if self.debug:
            pprint(self.metaedges)

    # For detailed penalty and count information
    # Each cell(i,j) corresponds to the penalty / count of items at level i and level j
    def get_initial_level_table(self, is_symmetric):
        # There should be height + 1 rows and columns
        n = self.height + 1
        table = [[0] * n for _ in range(n)]
        # We do not check crossing between leaf node and metanode
        # Here is just for printing out this message
        for i in xrange(n - 1):
            table[-1][i] = 'NA'
            table[i][-1] = 'NA'
        # It is supposed to be a symmetric matrix so we only use upper half of it
        if is_symmetric:
            for i in xrange(n):
                for j in xrange(i):
                    table[i][j] = 'NA'
        return table

    # Get the penalty for overlap between a node (or a subgraph / meta-node) v and an edge e
    def get_node_edge_penalty(self, e, v):
        geom_v = v['geometry']
        geom_e = e['geometry']
        if geom_v.intersects(geom_e):
            isect = geom_v.intersection(geom_e)
            if isect.area > 0:
                # Metaedge that has area
                o = isect.area
                max_overlap = min(geom_e.area, geom_v.area)
            else:
                # Leaf edge (and degenerated metaedge)
                o = isect.length
                max_overlap = min(geom_e.length, v['diameter'])
            p = self.penalty_func(o, max_overlap)
            if self.debug:
                print '(meta-)node {} overlaps with edge {} (overlap area: {}, penalty: {})'.format(v, e, isect.length, p)
            return True, p
        else:
            return False, 0

    # Get the penalty for overlap between two (meta-)nodes v1 and v2, given that nodes are represented as circles
    def get_node_node_penalty(self, v1, v2):
        geom1 = v1['geometry']
        geom2 = v2['geometry']
        if geom1.intersects(geom2):
            isect = geom1.intersection(geom2)
            p = self.penalty_func(isect.area, min(geom1.area, geom2.area))
            if self.debug:
                print '(meta-)node {} overlaps with (meta-)node {} (overlap area: {}, penalty: {})'.format(v1, v2, isect.area, p)
            return True, p
        else:
            return False, 0

    # Get the penalty for edge intersection
    def get_edge_edge_penalty(self, e1, e2):
        geom1 = e1['geometry']
        geom2 = e2['geometry']
        if geom1.intersects(geom2):
            if geom1.length < EPSILON or geom2.length < EPSILON:
                # If the line is too short, we won't be able to compute the angle
                p = 0
            else:
                if geom1.geom_type == 'LineString' and geom2.geom_type == 'LineString':
                    angle = get_angle_between_line_segments(geom1, geom2)
                    p = self.angle_penalty_func(angle)
                else:
                    isect = geom1.intersection(geom2)
                    ax1 = get_main_axis(geom1)
                    ax2 = get_main_axis(geom2)
                    angle = get_angle_between_line_segments(ax1, ax2)
                    if geom1.geom_type == 'Polygon' and geom2.geom_type == 'Polygon':
                        o = isect.area
                        max_overlap = min(geom1.area, geom2.area)
                    else:
                        o = isect.length
                        max_overlap = min(ax1.length, ax2.length)
                    p = self.angle_penalty_func(angle) * self.penalty_func(o, max_overlap)

            if self.debug:
                print 'Edge {} intersects with edge {}: angle {} (deg) penalty {}'.format(e1, e2, angle * 180 / math.pi, p)
            return True, p
        else:
            return False, 0

    # Get the overall node-node penalty and count for the whole graph
    def get_graph_node_node_penalty(self):
        penalty = 0
        count = 0
        penalty_lvl = self.get_initial_level_table(True)
        count_lvl = self.get_initial_level_table(True)

        for i, n1 in enumerate(self.leaf_nodes):
            # leaf node x leaf node
            for j in xrange(i + 1, len(self.leaf_nodes)):       # Make sure no duplicate pairs of nodes are considered
                n2 = self.leaf_nodes[j]
                is_isect, p = self.get_node_node_penalty(n1, n2)
                if is_isect:
                    count += 1
                    penalty += self.weight_func(self.height - 1) * p
                    count_lvl[-1][-1] += 1
                    penalty_lvl[-1][-1] += p

            # leaf node x subgraph
            # for metanode_id in self.metanodes:
            #     if metanode_id != self.root:
            #         mn = self.metanodes[metanode_id]
            #         if n1['id'] not in mn['leaf_nodes']:
            #             is_isect, p = self.get_node_node_penalty(n1, mn)
            #             if is_isect:
            #                 count += 1
            #                 lvl = mn['level']
            #                 penalty += self.weight_func(lvl) * p
            #                 count_lvl[lvl][-1] += 1
            #                 penalty_lvl[lvl][-1] += p

        for id1, mn1 in self.metanodes.iteritems():
            if id1 != self.root:
                for id2, mn2 in self.metanodes.iteritems():
                    if id2 != self.root and id1 < id2 and id2 not in mn1['desc_metanodes'] and id1 not in mn2['desc_metanodes']:
                        is_isect, p = self.get_node_node_penalty(mn1, mn2)
                        if is_isect:
                            count += p > 0
                            # Assuming weight function takes the higher one in the hierarchy
                            lvl1 = mn1['level']
                            lvl2 = mn2['level']
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
        # Row is node level, column is edge level
        penalty_lvl = self.get_initial_level_table(False)
        count_lvl = self.get_initial_level_table(False)

        # between leaf edge and leaf node
        for e in self.edges:
            s, t = e['ends']
            if s != t:
                for node in self.leaf_nodes:
                    if node['id'] != s and node['id'] != t:
                        is_isect, p = self.get_node_edge_penalty(e, node)
                        if is_isect:
                            count += 1
                            penalty += self.weight_func(self.height - 1) * p
                            count_lvl[-1][-1] += 1
                            penalty_lvl[-1][-1] += p

        # between metaedge and metanode
        for eid, e in self.metaedges.iteritems():
            s, t = e['ends']
            if s != t:
                for metanode_id, mn in self.metanodes.iteritems():
                    if metanode_id != self.root and metanode_id != s and metanode_id != t:
                        is_isect, p = self.get_node_edge_penalty(e, mn)
                        if is_isect:
                            count += 1
                            penalty += self.weight_func(min(mn['level'], e['level'])) * p
                            count_lvl[mn['level']][e['level']] += 1
                            penalty_lvl[mn['level']][e['level']] += p

        return {'total_penalty': penalty, 'penalty_by_level': penalty_lvl,
                'total_count': count, 'count_by_level': count_lvl}

    def get_graph_edge_edge_penalty(self):
        penalty = 0
        count = 0
        penalty_lvl = self.get_initial_level_table(True)
        count_lvl = self.get_initial_level_table(True)

        # between leaf edges
        for i, e1 in enumerate(self.edges):
            s, t = e1['ends']
            for j in xrange(i + 1, len(self.edges)):
                e2 = self.edges[j]
                # Make sure e1 and e2 do not connect the same node and they are not self connecting edges
                if s not in e2['ends'] and t not in e2['ends'] and s != t and e2['ends'][0] != e2['ends'][1]:
                    is_intersect, p = self.get_edge_edge_penalty(e1, e2)
                    if is_intersect:
                        count += 1
                        penalty += p
                        count_lvl[-1][-1] += 1
                        penalty_lvl[-1][-1] += p
        # between metaedges
        # TODO do we exclude the degenerate case? Otherwise the leaf edge would be counted multiple times?
        for eid1, e1 in self.metaedges.iteritems():
            s1, t1 = e1['ends']
            for eid2, e2 in self.metaedges.iteritems():
                if eid1 < eid2 and s1 not in e2['ends'] and t1 not in e2['ends']:
                    is_intersect, p = self.get_edge_edge_penalty(e1, e2)
                    if is_intersect:
                        count += 1
                        min_lvl = min(e1['level'], e2['level'])
                        max_lvl = max(e1['level'], e2['level'])
                        penalty += self.weight_func(min_lvl) * p
                        # Fill the upper-right triangle of the counting table
                        count_lvl[min_lvl][max_lvl] += 1
                        penalty_lvl[min_lvl][max_lvl] += p

        return {'total_penalty': penalty, 'penalty_by_level': penalty_lvl,
                'total_count': count, 'count_by_level': count_lvl}


# Print out the penalty and count by level
def print_by_level(p, c, is_symmetric):
    n = len(p[0])
    header_format = '\t{:5}' + '{:>10}' * (n - 1)
    # row_format = '\t{:5}' + '{:>10.2f}' * (n - 1)
    print '\tPenalty by level (max level corresponds to leaf, level 0 to the whole graph, before level weighting):'
    print header_format.format('level', *range(1, n))
    for i in range(1, n):
        row_format = '\t{:5}'
        for j in range(1, n):
            if type(p[i][j]) is str:
                row_format += '{:>10}'
            else:
                row_format += '{:>10.2f}'
        print row_format.format(i, *p[i][1:])
    print

    print '\tCount by level:'
    row_format = '\t{:5}' + '{:>10}' * (n - 1)
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
    print_by_level(nn['penalty_by_level'], nn['count_by_level'], True)

    ne = metrics.get_graph_node_edge_penalty()
    print 'Node-edge penalty: {:10.2f}   count: {:7}'.format(ne['total_penalty'], ne['total_count'])
    print_by_level(ne['penalty_by_level'], ne['count_by_level'], False)

    ee = metrics.get_graph_edge_edge_penalty()
    print 'Edge-edge penalty: {:10.2f}   count: {:7}'.format(ee['total_penalty'], ee['total_count'])
    print_by_level(ee['penalty_by_level'], ee['count_by_level'], True)

    print '===== END ====='
    print


def run_store_print(file_dir, filename, **metrics_args):
    data_path = os.path.join(file_dir, filename + '.tlp')
    # image_path = os.path.join(file_dir, filename + '.png')
    json_path = os.path.join(file_dir, filename + '_result.json')

    graph = tlp.loadGraph(data_path)
    metrics = MultiLevelMetrics(graph, **metrics_args)
    print '===== ', filename, ' ====='
    print '#nodes: {}  #edges: {}  height of node hiearachy: {}'.format(graph.numberOfNodes(), graph.numberOfEdges(), metrics.height)
    print

    json_data = {
        'tlpFile': filename + '.tlp',           # only the filename not the full path
        'graph': {
            'numberOfNodes': graph.numberOfNodes(),
            'numberOfEdges': graph.numberOfEdges(),
            'numberOfLevels': metrics.height,
        },
        'metrics': {}
    }

    nn = metrics.get_graph_node_node_penalty()
    json_data['metrics']['nn'] = nn
    print 'Node-node penalty: {:10.2f}   count: {:7}'.format(nn['total_penalty'], nn['total_count'])
    print_by_level(nn['penalty_by_level'], nn['count_by_level'], True)

    ne = metrics.get_graph_node_edge_penalty()
    json_data['metrics']['ne'] = ne
    print 'Node-edge penalty: {:10.2f}   count: {:7}'.format(ne['total_penalty'], ne['total_count'])
    print_by_level(ne['penalty_by_level'], ne['count_by_level'], False)

    ee = metrics.get_graph_edge_edge_penalty()
    json_data['metrics']['ee'] = ee
    print 'Edge-edge penalty: {:10.2f}   count: {:7}'.format(ee['total_penalty'], ee['total_count'])
    print_by_level(ee['penalty_by_level'], ee['count_by_level'], True)

    json.dump(json_data, open(json_path, 'w'))

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

    run_and_print('../data/test2.tlp', penalty_func_type='linear', debug=True)
