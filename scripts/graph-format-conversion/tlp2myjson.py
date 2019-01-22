# This file runs at "multilevel-metric" environment (Python 2)
# Expose a method to convert a tlp file to json
# Require packages: tlp, shapely

from tulip import tlp
from shapely.geometry import *
import re
import json
import sys
import os


def convert(input_path, subgraph_id=None, leaf_only=False):
    whole_graph = tlp.loadGraph(input_path)
    if subgraph_id is not None:
        graph = whole_graph.getSubGraph(subgraph_id)
    else:
        graph = whole_graph
    print(graph)

    # Retrieve nodes and edges from graph and construct Shapely geometries
    view_layout = graph.getLayoutProperty('viewLayout')
    view_size = graph.getSizeProperty('viewSize')

    leaf_nodes = [{'id': n.id, 'parent_metanode': None,        # fulfill later
                   'geometry': Point(view_layout[n].x(), view_layout[n].y()).buffer(view_size[n][0] / 2.0, cap_style=CAP_STYLE.round),
                   'diameter': view_size[n][0]}
                  for n in graph.nodes()]

    edges = []
    check_dup = {}
    for e in graph.getEdges():
        src, tgt = graph.ends(e)
        if src.id > tgt.id:
            tmp = src
            src = tgt
            tgt = tmp
        edge_id = '{}-{}'.format(src.id, tgt.id)
        # remove duplicate and self-connecting edges
        if edge_id not in check_dup and src.id != tgt.id:
            edges.append({'id': e.id,
                          'ends': (src.id, tgt.id),
                          'geometry': LineString([(view_layout[src].x(), view_layout[src].y()),
                                                  (view_layout[tgt].x(), view_layout[tgt].y())])})
            check_dup[edge_id] = True

    bbox = tlp.computeBoundingBox(graph)
    root = graph.getId()
    height = {'a': 1}
    metanodes = {}

    # Construct a simple node (graph) hierarchy data structure from the tulip graph and count levels
    # This is the same level counting method in the Bourqui multi-level force layout paper.

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

        height['a'] = max(height['a'], cur_height + 1)
        for s in g.getSubGraphs():
            dfs(s, cur_height + 1)
            metanodes[s.getId()]['parent_metanode'] = g.getId()

        # Add the field parent_metanode to the leaf node
        for leaf in g.getNodes():
            tmp = leaf_nodes[leaf.id]
            if tmp['parent_metanode'] is None:
                tmp['parent_metanode'] = g.getId()

        # Compute convex hull of this sub-graph in post-order
        if g.numberOfSubGraphs() == 0:
            # compute a convex hull of its leaf nodes
            coords = tlp.computeConvexHull(g)
            node['geometry'] = Polygon([(c.x(), c.y()) for c in coords])
        else:
            # union the convex hull of its sub-graphs
            node['geometry'] = MultiPolygon([metanodes[s.getId()]['geometry'] for s in g.getSubGraphs()]).convex_hull

        # Note that we don't compute the real diameter for a polygon, but instead, only use the diagonal of
        # the axis aligned bounding box to approximate the diameter, which is cheap to compute
        bbox = node['geometry'].bounds
        node['diameter'] = Point(bbox[0], bbox[1]).distance(Point(bbox[2], bbox[3]))

        metanodes[g.getId()] = node

    if not leaf_only:
        dfs(graph, root)

    # Output json file at the same directory with same filename but "json" extension
    output_path = re.sub(r'\.tlp$', '.json', input_path)

    # Use the mapping function from shapely to serialize the geometry objects
    for n in leaf_nodes:
        n['geometry'] = mapping(n['geometry'])
    for e in edges:
        e['geometry'] = mapping(e['geometry'])
    for _, n in metanodes.items():
        n['geometry'] = mapping(n['geometry'])

    json_data = {
        'leaf_nodes': leaf_nodes,
        'edges': edges,
        'height': height['a'],
        'root': root,
        'metanodes': metanodes,
        'bounding_box': [[bbox[0].x(), bbox[0].y()], [bbox[1].x(), bbox[1].y()]]
    }
    json.dump(json_data, open(output_path, 'w'))
    print('Converted to ', output_path, ' #nodes:', len(leaf_nodes), ' #edges: ', len(edges), ' height: ', height['a'])


if __name__ == '__main__':
    tlp_file = '../../../data/test/test2.tlp' if len(sys.argv) < 2 else sys.argv[1]
    subgraph_id = None if len(sys.argv) < 3 else int(sys.argv[2])

    if os.path.isdir(tlp_file):
        # convert every tlp file under this directory
        for filename in os.listdir(tlp_file):
            if filename.endswith('.tlp'):
                convert(os.path.join(tlp_file, filename))
    elif os.path.isfile(tlp_file):
        convert(tlp_file, subgraph_id=subgraph_id)
    else:
        print('Error: no file or directory found')
