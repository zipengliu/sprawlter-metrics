# This file runs on Python 3
# Require packages: shapely, isect_segment (by ideasman42)

from geometric import *
from shapely.geometry import *
import math
import json
import os
from time import process_time as timer
from time import time as wall_time
from poly_point_isect import isect_segments_include_segments, isect_segments__naive, isect_seg_seg_v2_point


ALPHA = 0.2
GLANCING_ANGLE_PENALTY = 5
# These coefficients for edge-edge penalty are fixed because the GLANCING_ANGLE_PENALTY (m) is fixed
ANGLE_QUAD_COEFFICIENT = 4 * (1 - ALPHA) * GLANCING_ANGLE_PENALTY / (math.pi * math.pi)
ANGLE_LOG_COEFFICIENT = (1 - ALPHA) * GLANCING_ANGLE_PENALTY / math.log(math.pi / 2 + 1)

LINEAR_DECAY_RATE = -0.1
EXPONENTIAL_DECAY_RATE = 0.5

USE_LOG = False


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
    if x < EPSILON or m < EPSILON:
        return 0
    else:
        # calculate the log coefficient because m can be different for different overlaps
        c = (1 - ALPHA) * m / math.log(m + 1)
        return c * math.log(x + 1) + ALPHA * m


# Penalty function for edge edge crossing
# Linear.  x the acute crossing angle is [0, PI / 2]
# Note that angle can be zero, which means part of the edges stack up / collinear
def angle_linear_func(x, m=GLANCING_ANGLE_PENALTY):
    return m * (ALPHA - 1) / (math.pi / 2) * x + m


# Quadratic function: p(x) = -kx^2 + m
def angle_quadratic_func(x, m=GLANCING_ANGLE_PENALTY):
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


# a decorator for performance timing
def timeit(func):
    def timed(*args, **kw):
        ts = timer()
        result = func(*args, **kw)
        te = timer()

        result['execution_time'] = te - ts
        return result
    return timed


class MultiLevelMetrics:

    def __init__(self, json_path, penalty_func_type = 'piecewise-linear', angle_penalty_func_type = 'linear',
                 hierarchical_weight_func_type = 'uniform', debug=False):
        self.debug = debug

        # Import the coordinates of graph elements
        json_data = json.load(open(json_path))
        # print(json_data)
        for n in json_data['leaf_nodes']:
            n['geometry'] = shape(n['geometry'])
        for e in json_data['edges']:
            e['geometry'] = shape(e['geometry'])
        for _, n in json_data['metanodes'].items():
            n['geometry'] = shape(n['geometry'])
        for k, v in json_data.items():
            setattr(self, k, v)

        # Convert to format that is friendly to isect implementation
        # self.edges_isect = [tuple(list(e['geometry'].coords) + [e['id']]) for e in self.edges]
        self.edges_isect = [tuple(e['geometry'].coords) for e in self.edges]

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
        elif hierarchical_weight_func_type == 'none':
            self.weight_func = lambda x: 1
        else:
            self.weight_func = get_exponential_decay_func(EXPONENTIAL_DECAY_RATE, self.height)

    # For detailed penalty and count information
    # Each cell(i,j) corresponds to the penalty / count of items at level i and level j
    def get_initial_level_table(self, is_symmetric, is_node_node):
        # There should be height + 1 rows and columns
        n = self.height + 1
        table = [[0] * n for _ in range(n)]
        # We do not check crossing between leaf node and metanode
        # Here is just for printing out this message
        if is_node_node:
            for i in range(n - 1):
                table[-1][i] = 'NA'
                table[i][-1] = 'NA'
        # It is supposed to be a symmetric matrix so we only use upper half of it
        if is_symmetric:
            for i in range(n):
                for j in range(i):
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
                if 'desc_metanodes' not in v:
                    node_str = 'node'
                else:
                    node_str = 'metanode'
                print('{} {} overlaps with edge {} (overlap area: {}, penalty: {})'
                      .format(node_str, v['id'], e['id'], isect.length, p))
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
                print('(meta-)node {} overlaps with (meta-)node {} (overlap area: {}, penalty: {})'
                      .format(v1['id'], v2['id'], isect.area, p))
            return True, p
        else:
            return False, 0

    # Get the penalty for edge intersection
    def get_edge_edge_penalty(self, e1, e2):
        geom1 = e1['geometry']
        geom2 = e2['geometry']

        # If the line is too short, we won't be able to compute the angle but it can count as one intersection
        # if geom1.length < EPSILON or geom2.length < EPSILON:
        #     return False, 0

        if geom1.intersects(geom2):
            # x = geom1.intersection(geom2)
            # se0 = Point(geom1.coords[0])
            # se1 = Point(geom1.coords[1])
            # se2 = Point(geom2.coords[0])
            # se3 = Point(geom2.coords[1])
            # # If the intersection is at the ends of both segments, exclude it
            # # TODO why?
            # if (x.almost_equals(se0, 10) or x.almost_equals(se1, 10)) and (x.almost_equals(se2, 10) or x.almost_equals(se3, 10)):
            #     print('Edge {} intersects with edge {} at the segment endings'.format(e1['id'], e2['id']))
            #     return False, 0

            angle = get_angle_between_line_segments(geom1, geom2)
            p = self.angle_penalty_func(angle)

            if self.debug:
                print('Edge {} intersects with edge {}: angle {} (deg) penalty {}'
                      .format(e1['id'], e2['id'], angle * 180 / math.pi, p))
            return True, p
        else:
            return False, 0

    # Get the overall node-node penalty and count for the whole graph
    @timeit
    def get_graph_node_node_penalty(self):
        penalty = 0
        count = 0
        penalty_lvl = self.get_initial_level_table(True, True)
        count_lvl = self.get_initial_level_table(True, True)

        for i, n1 in enumerate(self.leaf_nodes):
            # leaf node x leaf node
            for j in range(i + 1, len(self.leaf_nodes)):       # Make sure no duplicate pairs of nodes are considered
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

        for id1, mn1 in self.metanodes.items():
            if id1 != self.root:
                for id2, mn2 in self.metanodes.items():
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

    @timeit
    def get_graph_node_edge_penalty(self):
        penalty = 0
        count = 0
        # Row is node level, column is edge level
        penalty_lvl = self.get_initial_level_table(False, False)
        count_lvl = self.get_initial_level_table(False, False)

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

                # the keys in mn['leaf_nodes'] are strings, but s and t are integers
                s_str = str(s)
                t_str = str(t)
                for metanode_id, mn in self.metanodes.items():
                    if int(metanode_id) != self.root and s_str not in mn['leaf_nodes'] and t_str not in mn['leaf_nodes']:
                        is_isect, p = self.get_node_edge_penalty(e, mn)
                        if is_isect:
                            count += 1
                            # penalty += self.weight_func(min(mn['level'], e['level'])) * p
                            # count_lvl[mn['level']][e['level']] += 1
                            # penalty_lvl[mn['level']][e['level']] += p
                            penalty += self.weight_func(mn['level']) * p
                            count_lvl[mn['level']][-1] += 1
                            penalty_lvl[mn['level']][-1] += p

        return {'total_penalty': penalty, 'penalty_by_level': penalty_lvl,
                'total_count': count, 'count_by_level': count_lvl}

    @timeit
    def get_graph_edge_edge_penalty(self):
        penalty = 0
        count = 0
        crossings = []
        # penalty_lvl = self.get_initial_level_table(True, False)
        # count_lvl = self.get_initial_level_table(True, False)

        s = timer()
        intersections = isect_segments_include_segments(self.edges_isect)
        e = timer()
        print('B-O takes ', e - s, 'seconds')
        print('# intersection points: ', len(intersections))
        if USE_LOG:
            json.dump(intersections, open('intersections.json', 'w'))
        if self.debug:
            print(intersections)
        for isect in intersections:
            segments = isect[1]
            # There might be multiple line segments intersect at the same point
            for i in range(len(segments) - 1):
                for j in range(i + 1, len(segments)):
                    angle = get_angle_between_line_segments_v2(segments[i], segments[j])
                    p = self.angle_penalty_func(angle)
                    crossings.append((segments[i][0], segments[j][1]))
                    count += 1
                    penalty += p

                    if self.debug:
                        # we cannot find out the edge id easily b/c use of 3rd party lib
                        print('Edge xx intersects with edge xx: angle {} (deg) penalty {}'.format(angle * 180 / math.pi, p))

        if USE_LOG:
            json.dump(crossings, open('test_bo.json', 'w'))
        return {'total_penalty': penalty, 'total_count': count}

    # @timeit
    # def get_graph_edge_edge_penalty_naive_v2(self):
    #     penalty = 0
    #     count = 0
    #     crossings = []
    #     # penalty_lvl = self.get_initial_level_table(True, False)
    #     # count_lvl = self.get_initial_level_table(True, False)
    #
    #     s = timer()
    #     intersections = isect_segments__naive(self.edges_isect)
    #     e = timer()
    #     print('# intersection points: ', len(intersections))
    #     if USE_LOG:
    #         json.dump(intersections, open('intersections_naive_v2.json', 'w'))
    #     if self.debug:
    #         print(intersections)
    #     for isect in intersections:
    #         segments = isect[1]
    #         # There might be multiple line segments intersect at the same point
    #         for i in range(len(segments) - 1):
    #             for j in range(i + 1, len(segments)):
    #                 angle = get_angle_between_line_segments_v2(segments[i], segments[j])
    #                 p = self.angle_penalty_func(angle)
    #                 crossings.append((segments[i][2], segments[j][2]))
    #                 count += 1
    #                 penalty += p
    #
    #                 if self.debug:
    #                     # we cannot find out the edge id easily b/c use of 3rd party lib
    #                     print('Edge xx intersects with edge xx: angle {} (deg) penalty {}'.format(angle * 180 / math.pi, p))
    #
    #     if USE_LOG:
    #         json.dump(crossings, open('test_naive_v2.json', 'w'))
    #     return {'total_penalty': penalty, 'total_count': count}

    @timeit
    def get_graph_edge_edge_penalty_naive(self):
        penalty = 0
        count = 0
        # crossings = []

        # between leaf edges
        for i, e1 in enumerate(self.edges):
            s, t = e1['ends']
            if s != t:
                for j in range(i + 1, len(self.edges)):
                    e2 = self.edges[j]
                    if e2['ends'][0] != e2['ends'][1]:
                        # Make sure e1 and e2 do not connect the same node and they are not self connecting edges
                        if s not in e2['ends'] and t not in e2['ends']:
                            is_intersect, p = self.get_edge_edge_penalty(e1, e2)
                            if is_intersect:
                                # crossings.append((e1['id'], e2['id']))
                                count += 1
                                penalty += p
        # if USE_LOG:
        #     json.dump(crossings, open('test_mine.json', 'w'))
        return {'total_penalty': penalty, 'total_count': count}


# Print out the penalty and count by level
def print_by_level(p, c, is_symmetric):
    n = len(p[0])
    header_format = '\t{:5}' + '{:>10}' * (n - 1)
    # row_format = '\t{:5}' + '{:>10.2f}' * (n - 1)
    print('\tPenalty by level (max level corresponds to leaf, level 0 to the whole graph, before level weighting):')
    print(header_format.format('level', *range(1, n)))
    for i in range(1, n):
        row_format = '\t{:5}'
        for j in range(1, n):
            if type(p[i][j]) is str:
                row_format += '{:>10}'
            else:
                row_format += '{:>10.2f}'
        print(row_format.format(i, *p[i][1:]))
    print()

    print('\tCount by level:')
    row_format = '\t{:5}' + '{:>10}' * (n - 1)
    print(header_format.format('level', *range(1, n)))
    for i in range(1, n):
        print(row_format.format(i, *c[i][1:]))
    print()


def run_store_print(file_dir, filename, **metrics_args):
    data_path = os.path.join(file_dir, filename + '.json')
    # image_path = os.path.join(file_dir, filename + '.png')
    json_path = os.path.join(file_dir, filename + '_result.json')

    metrics = MultiLevelMetrics(data_path, **metrics_args)
    print('===== ', filename, ' =====')
    print('#nodes: {}  #edges: {}  height of hierarchy: {}  root ID: {}'.format(len(metrics.leaf_nodes), len(metrics.edges), metrics.height, metrics.root))
    print()

    json_data = {
        'tlpFile': filename + '.tlp',           # only the filename not the full path
        'graph': {
            'numberOfNodes': len(metrics.leaf_nodes),
            'numberOfMetaNodes': len(metrics.metanodes.keys()),
            'numberOfEdges': len(metrics.edges),
            'numberOfLevels': metrics.height,
        },
        'start_time': wall_time(),
        'metrics': {
            'area': metrics.bounding_box
        },
        'parameters': {
            'alpha': ALPHA,
            'glancingAnglePenalty': GLANCING_ANGLE_PENALTY,
        }
    }
    for k, v in metrics_args.items():
        json_data['parameters'][k] = v

    nn = metrics.get_graph_node_node_penalty()
    # nn = {}
    json_data['metrics']['nn'] = nn
    print('Node-node penalty: {:10.2f}   count: {:7}  execution time: {:6.2f}'
          .format(nn['total_penalty'], nn['total_count'], nn['execution_time']))
    print_by_level(nn['penalty_by_level'], nn['count_by_level'], True)

    ne = metrics.get_graph_node_edge_penalty()
    # ne = {}
    json_data['metrics']['ne'] = ne
    print('Node-edge penalty: {:10.2f}   count: {:7}  execution time: {:6.2f}'
          .format(ne['total_penalty'], ne['total_count'], ne['execution_time']))
    print_by_level(ne['penalty_by_level'], ne['count_by_level'], False)

    # Bentlety-Ottamann
    # ee = metrics.get_graph_edge_edge_penalty()
    # json_data['metrics']['ee'] = ee
    # print('Edge-edge penalty: {:10.2f}   count: {:7}  execution time: {:6.2f}'
    #       .format(ee['total_penalty'], ee['total_count'], ee['execution_time']))

    # My naive square time implementation
    ee2 = metrics.get_graph_edge_edge_penalty_naive()
    json_data['metrics']['ee'] = ee2
    print('Edge-edge penalty (quadratic algorithm): {:10.2f}   count: {:7}  execution time: {:6.2f}'
          .format(ee2['total_penalty'], ee2['total_count'], ee2['execution_time']))

    json_data['end_time'] = wall_time()
    json.dump(json_data, open(json_path, 'w'))

    print('===== END =====')
    print()


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

    # run_store_print('../../data/coauthor', 'sfdp', penalty_func_type='linear', debug=True)
    # run_store_print('../../data/real-world-compiled/snap-main-comp', 'snap-email-eu-core-main-comp-grouseflocks-open-6',
    #                penalty_func_type='linear', debug=False)
    run_store_print('../../data/real-world-compiled/grouseflocks', 'grouseflocks-ivOrigins-grouseflocks-open-4',
                   penalty_func_type='linear', debug=False)
