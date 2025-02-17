""" Find shortest path given a from node and a to node

The underlying C++ engine is a special implementation of the deque 
implementation in C++ and built into path_engine.dll.
"""


import ctypes
import platform
from os import path
from time import time

from .consts import MAX_LABEL_COST


__all__ = [
    'single_source_shortest_path',
    'output_path_sequence',
    'find_shortest_path',
    'find_path_for_agents',
    'benchmark_apsp'
]


_os = platform.system()
if _os.startswith('Windows'):
    _dll_file = path.join(path.dirname(__file__), 'bin/path_engine.dll')
elif _os.startswith('Linux'):
    _dll_file = path.join(path.dirname(__file__), 'bin/path_engine.so')
elif _os.startswith('Darwin'):
    # check CPU is Intel or Apple Silicon
    if platform.machine().startswith('x86_64'):
        _dll_file = path.join(path.dirname(__file__), 'bin/path_engine_x86.dylib')
    else:
        _dll_file = path.join(path.dirname(__file__), 'bin/path_engine_arm.dylib')
else:
    raise Exception('Please build the shared library compatible to your OS\
                    using source files in engine_cpp!')

_cdll = ctypes.cdll.LoadLibrary(_dll_file)

# set up the argument types for the shortest path function in dll.
_cdll.shortest_path_n.argtypes = [
    ctypes.c_int,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_wchar_p),
    ctypes.POINTER(ctypes.c_double),
    ctypes.POINTER(ctypes.c_double),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.c_wchar_p,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int
]


def _optimal_label_correcting_CAPI(G, origin_node_no, departure_time=0):
    """ call the deque implementation of MLC written in cpp

    node_label_cost, node_predecessor, and link_predecessor are still
    initialized in shortest_path() even the source node has no outgoing links.
    """
    _cdll.shortest_path_n(origin_node_no,
                          G.get_node_size(),
                          G.get_from_node_no_arr(),
                          G.get_to_node_no_arr(),
                          G.get_first_links(),
                          G.get_last_links(),
                          G.get_sorted_link_no_arr(),
                          G.get_allowed_uses(),
                          G.get_link_costs(),
                          G.get_node_label_costs(),
                          G.get_node_preds(),
                          G.get_link_preds(),
                          G.get_queue_next(),
                          G.get_agent_type_name(),
                          MAX_LABEL_COST,
                          G.get_last_thru_node(),
                          departure_time)


def single_source_shortest_path(G, origin_node_id):
    origin_node_no = G.get_node_no(origin_node_id)
    G.allocate_for_CAPI()
    _optimal_label_correcting_CAPI(G, origin_node_no)


def output_path_sequence(G, to_node_id, type='node'):
    """ output shortest path in terms of node sequence or link sequence

    Note that this function returns GENERATOR rather than list.
    """
    path = []
    curr_node_no = G.map_id_to_no[to_node_id]

    if type.startswith('node'):
        # retrieve the sequence backwards
        while curr_node_no >= 0:
            path.append(curr_node_no)
            curr_node_no = G.node_preds[curr_node_no]
        # reverse the sequence
        for node_no in reversed(path):
            yield G.map_no_to_id[node_no]
    else:
        # retrieve the sequence backwards
        curr_link_no = G.link_preds[curr_node_no]
        while curr_link_no >= 0:
            path.append(curr_link_no)
            curr_node_no = G.node_preds[curr_node_no]
            curr_link_no = G.link_preds[curr_node_no]
        # reverse the sequence
        for link_no in reversed(path):
            yield G.links[link_no].get_link_id()


def _get_path_cost(G, to_node_id):
    to_node_no = G.map_id_to_no[to_node_id]

    return G.node_label_cost[to_node_no]


def find_shortest_path(G, from_node_id, to_node_id, seq_type='node'):
    if from_node_id not in G.map_id_to_no:
        raise Exception(f'Node ID: {from_node_id} not in the network')
    if to_node_id not in G.map_id_to_no:
        raise Exception(f'Node ID: {to_node_id} not in the network')

    single_source_shortest_path(G, from_node_id)

    path_cost = _get_path_cost(G, to_node_id)
    if path_cost >= MAX_LABEL_COST:
        return f'distance: infinity | path: '

    path = ';'.join(
        str(x) for x in output_path_sequence(G, to_node_id, seq_type)
    )

    if seq_type.startswith('node'):
        return f'distance: {path_cost:.2f} mi | node path: {path}'
    else:
        return f'distance: {path_cost:.2f} mi | link path: {path}'


def find_path_for_agents(G, column_pool):
    """ find and set up shortest path for each agent

    the internal node and links will be used to set up the node sequence and
    link sequence respectively

    Note that we do not cache the predecessors and label cost even some agents
    may share the same origin and each call of the single-source path algorithm
    will calculate the shortest path tree from the source node.
    """
    if G.get_agent_count() == 0:
        print('setting up individual agents')
        G.setup_agents(column_pool)

    from_node_id_prev = ''
    for agent in G.agents:
        from_node_id = agent.o_node_id
        to_node_id = agent.d_node_id

        # just in case agent has the same origin and destination
        if from_node_id == to_node_id:
            continue

        if from_node_id not in G.map_id_to_no:
            raise Exception(f'Node ID: {from_node_id} not in the network')
        if to_node_id not in G.map_id_to_no:
            raise Exception(f'Node ID: {to_node_id} not in the network')

        # simple caching strategy
        # if the current from_node_id is the same as from_node_id_prev,
        # then there is no need to redo shortest path calculation.
        if from_node_id != from_node_id_prev:
            from_node_id_prev = from_node_id
            single_source_shortest_path(G, from_node_id)

        node_path = []
        link_path = []

        curr_node_no = G.map_id_to_no[to_node_id]
        # set up the cost
        agent.path_cost = G.node_label_cost[curr_node_no]

        # retrieve the sequence backwards
        while curr_node_no >= 0:
            node_path.append(curr_node_no)
            curr_link_no = G.link_preds[curr_node_no]
            if curr_link_no >= 0:
                link_path.append(curr_link_no)
            curr_node_no = G.node_preds[curr_node_no]

        # make sure it is a valid path
        if not link_path:
            continue

        agent.node_path = [x for x in node_path]
        agent.link_path = [x for x in link_path]


def benchmark_apsp(G):
    st = time()

    for k in G.map_id_to_no:
        single_source_shortest_path(G, k)

    print(f'processing time of finding all-pairs shortest paths: {time()-st:.4f} s')