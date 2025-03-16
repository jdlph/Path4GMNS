""" The Python interface connecting the C++ path engine and other Python APIs """
import ctypes
import platform
from os import path
from time import time

from .consts import MAX_LABEL_COST
from .utils import _convert_str_to_int, InvalidRecord


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
                    using the source file in engine!')

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


# simple caching for _single_source_shortest_path()
_prev_cost_type = 'time'


def _optimal_label_correcting_CAPI(G, origin_node_no, departure_time=0):
    """ call the deque implementation of MLC written in cpp

    node_label_cost, node_predecessor, and link_predecessor are still
    initialized in shortest_path_n() even the source node has no outgoing links.
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


def single_source_shortest_path(G, orig_node_id, cost_type='time'):
    G.allocate_for_CAPI()

    global _prev_cost_type
    if _prev_cost_type != cost_type:
        G.init_link_costs(cost_type)
        _prev_cost_type = cost_type

    orig_node_no = G.get_node_no(orig_node_id)
    _optimal_label_correcting_CAPI(G, orig_node_no)


def output_path_sequence(G, to_node_id, seq_type='node'):
    """ output shortest path in terms of node sequence or link sequence

    Note that this function returns GENERATOR rather than list.
    """
    path = []
    curr_node_no = G.map_id_to_no[to_node_id]

    if seq_type.startswith('node'):
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


def find_shortest_path(G, from_node_id, to_node_id, seq_type, cost_type):
    if from_node_id not in G.map_id_to_no:
        raise Exception(f'Node ID: {from_node_id} not in the network')
    if to_node_id not in G.map_id_to_no:
        raise Exception(f'Node ID: {to_node_id} not in the network')

    single_source_shortest_path(G, from_node_id, cost_type)

    path_cost = G.get_path_cost(to_node_id, cost_type)
    if path_cost >= MAX_LABEL_COST:
        return f'path {cost_type}: infinity | path: '

    path = _get_path_sequence_str(G, to_node_id, seq_type)

    unit = 'minutes'
    if cost_type.startswith('dis'):
        unit = G.get_length_unit() + 's'

    if seq_type.startswith('node'):
        return f'path {cost_type}: {path_cost:.4f} {unit} | node path: {path}'
    else:
        return f'path {cost_type}: {path_cost:.4f} {unit} | link path: {path}'


def find_path_for_agents(G, column_pool, cost_type):
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
            single_source_shortest_path(G, from_node_id, cost_type)

        # set up the cost
        agent.path_cost = G.get_path_cost(to_node_id, cost_type)

        node_path = []
        link_path = []

        curr_node_no = G.map_id_to_no[to_node_id]
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


def _get_path_sequence_str(G, to_node_id, seq_type):
    return ';'.join(str(x) for x in output_path_sequence(G, to_node_id, seq_type))


def get_shortest_path_tree(G, from_node_id, seq_type, cost_type, integer_node_id):
    """ compute the shortest path tree from the source node (from_node_id)

    it returns a dictionary, where key is to_node_id and value is the
    corresponding shortest path information (path cost and path details).

    Note that the source node itself is excluded from the dictionary keys.
    """
    if from_node_id not in G.map_id_to_no:
        raise Exception(f'Node ID: {from_node_id} not in the network')

    single_source_shortest_path(G, from_node_id, cost_type)

    if integer_node_id:
        sp_tree = {}
        for to_node_id in G.map_id_to_no:
            if to_node_id == from_node_id:
                continue

            try:
                to_node_id_int = _convert_str_to_int(to_node_id)
            except InvalidRecord:
                to_node_id_int = to_node_id

            sp_tree[to_node_id_int] = (
                G.get_path_cost(to_node_id, cost_type),
                _get_path_sequence_str(G, to_node_id, seq_type)
            )

        return sp_tree
    else:
        return {
            to_node_id : (
                G.get_path_cost(to_node_id, cost_type),
                _get_path_sequence_str(G, to_node_id, seq_type)
            )
            for to_node_id in G.map_id_to_no if to_node_id != from_node_id
        }


def benchmark_apsp(G):
    st = time()

    for k in G.map_id_to_no:
        # do not include centroids
        if G.map_id_to_no[k] >= G.get_last_thru_node():
            break
        
        single_source_shortest_path(G, k)

    print(f'processing time of finding all-pairs shortest paths: {time()-st:.4f} s')
