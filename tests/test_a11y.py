from path4gmns.accessibility import evaluate_accessibility, evaluate_equity
from path4gmns.utils import read_network


def test_multimodal_accessibility():
    network = read_network(input_dir='tests/fixtures')
    # multimodal accessibility evaluation
    evaluate_accessibility(network, output_dir='tests/tmp')

    # get accessible nodes and links starting from node 1 with a 5-minute
    # time window for the default mode auto (i.e., 'auto')
    network.get_accessible_nodes(1, 5)
    network.get_accessible_links(1, 5)

    # get accessible nodes and links starting from node 1 with a 15-minute
    # time window for mode walk (i.e., 'w')
    try:
        network.get_accessible_nodes(1, 15, 'w')
        network.get_accessible_links(1, 15, 'w')
    except Exception:
        pass


def test_unimodal_accessibility():
    network = read_network(input_dir='tests/fixtures')
    # accessibility evaluation for a target mode only
    evaluate_accessibility(network, single_mode=True, mode='auto')


def test_time_dependent_accessibility():
    network = read_network(input_dir='tests/fixtures')
    # time-dependent accessibility under the default mode auto
    # for demand period 0 (i.e., VDF_fftt1 in link.csv will be used in the
    # evaluation)
    evaluate_accessibility(network,
                           single_mode=True,
                           time_dependent=True,
                           output_dir='tests/tmp')

    # get accessible nodes and links starting from node 1 with a 5-minute
    # time window for the default mode auto for demand period 0
    network.get_accessible_nodes(1, 5, time_dependent=True)
    network.get_accessible_links(1, 5, time_dependent=True)

    # get accessible nodes and links starting from node 1 with a 15-minute
    # time window for mode walk (i.e., 'w') for demand period 0
    try:
        network.get_accessible_nodes(1, 15, 'w', time_dependent=True)
        network.get_accessible_links(1, 15, 'w', time_dependent=True)
    except Exception:
        pass


def test_multimodal_equity():
    network = read_network(input_dir='tests/fixtures')
    # multimodal equity evaluation under default time budget (60 min)
    evaluate_equity(network, output_dir='tests/tmp')


def test_unimodal_equity():
    network = read_network(input_dir='tests/fixtures')
    # equity evaluation for a target mode with time budget as 30 min
    evaluate_equity(network, single_mode=True, mode='auto', time_budget=30)