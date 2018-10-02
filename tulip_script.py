from tulip import tlp

# handy (but dirty?) way to import local python file
import sys, os
sys.path.append(os.path.abspath('/Users/zipeng/Documents/Visualization/MultilevelMetrics/code/'))
from multilevel_metrics import MultiLevelMetrics
# execfile('/Users/zipeng/Documents/Visualization/MultilevelMetrics/code/multilevel_metrics.py')


def main(graph):
    metrics = MultiLevelMetrics(graph, penalty_func_type='log', angle_penalty_func_type='quadratic',
                                hierarchical_weight_func_type='exponential')
    print '#nodes: {}  #edges: {}'.format(graph.numberOfNodes(), graph.numberOfEdges())

    nn = metrics.get_graph_node_node_penalty()
    print 'Node-node penalty: {:10.2f}   count: {:7}'.format(nn[0], nn[1])

    ne = metrics.get_graph_node_edge_penalty()
    print 'Node-edge penalty: {:10.2f}   count: {:7}'.format(ne[0], ne[1])

    ee = metrics.get_graph_edge_edge_penalty()
    print 'Edge-edge penalty: {:10.2f}   count: {:7}'.format(ee[0], ee[1])
    print
