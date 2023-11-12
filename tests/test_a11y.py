from path4gmns.accessibility import evaluate_accessibility, evaluate_equity
from path4gmns.utils import read_network


def test_accessibility():
    network = read_network(input_dir='tests/fixtures')

    # multimodal accessibility evaluation
    evaluate_accessibility(network, output_dir='tests/tmp')
    # accessibility evaluation for a target mode
    # evaluate_accessibility(network, single_mode=True, mode='auto')

    # get accessible nodes and links starting from node 1 with a 5-minute
    # time window for the default mode auto (i.e., 'auto')
    network.get_accessible_nodes(1, 5)
    network.get_accessible_links(1, 5)

    # get accessible nodes and links starting from node 1 with a 15-minute
    # time window for mode walk (i.e., 'w')
    network.get_accessible_nodes(1, 15, 'w')
    network.get_accessible_links(1, 15, 'w')


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

    # get accessible nodes and links starting from node 1 with a 15-minute
    # time window for mode walk (i.e., 'w') for demand period 0
    network.get_accessible_nodes(1, 15, 'w', time_dependent=True)


def test_equity():
    network = read_network(input_dir='tests/fixtures')

    # multimodal equity evaluation under default time budget (60 min)
    evaluate_equity(network, output_dir='tests/tmp')
    # equity evaluation for a target mode with time budget as 30 min
    try:
        evaluate_equity(network, single_mode=True, mode='auto', time_budget=30)
    except Exception:
        pass