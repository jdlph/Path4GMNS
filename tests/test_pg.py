from os import chdir, mkdir, remove
from os.path import isdir
from shutil import rmtree

from path4gmns.accessibility import evaluate_accessibility, evaluate_equity
from path4gmns.simulation import perform_simple_simulation

from path4gmns.utils import download_sample_data_sets, load_columns, \
                            load_demand, output_agent_trajectory,\
                            output_synthesized_demand, output_zones, \
                            read_network, read_zones

from path4gmns.zonesyn import network_to_zones


def test_download_sample_data_sets():
    chdir('tests')
    download_sample_data_sets()

    if not isdir('tmp'):
        mkdir('tmp')

    rmtree('data')
    chdir('..')


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

    # time-dependent accessibility under the default mode auto
    # for demand period 0 (i.e., VDF_fftt1 in link.csv will be used in the
    # evaluation)
    # evaluate_accessibility(network, single_mode=True, time_dependent=True)

    # it is equivalent to
    # evaluate_accessibility(network, single_mode=True,
    #                           time_dependent=True, demand_period_id=0)

    # get accessible nodes and links starting from node 1 with a 5-minute
    # time window for the default mode auto for demand period 0
    # network.get_accessible_nodes(1, 5, time_dependent=True)

    # get accessible nodes and links starting from node 1 with a 15-minute
    # time window for mode walk (i.e., 'w') for demand period 0
    # network.get_accessible_nodes(1, 15, 'w', time_dependent=True)


def test_equity():
    network = read_network(input_dir='tests/fixtures')

    # multimodal equity evaluation under default time budget (60 min)
    evaluate_equity(network, output_dir='tests/tmp')
    # equity evaluation for a target mode with time budget as 30 min
    # evaluate_equity(network, single_mode=True, mode='auto', time_budget=30)


def test_simulation():
    network = read_network(load_demand=True, input_dir='tests/fixtures')

    # column_gen_num = 20
    # column_update_num = 20
    # perform_column_generation(column_gen_num, column_update_num, network)

    # you can bypass the above perform_column_generation() and call
    # load_columns(network) if you have route_assignment.csv
    load_columns(network, input_dir='tests/tmp')
    perform_simple_simulation(network, 'uniform')

    output_agent_trajectory(network, output_dir='tests/tmp')


def test_zone_synthesis():
    network = read_network(input_dir='tests/fixtures')
    network_to_zones(network)

    output_zones(network, output_dir='tests/tmp')
    output_synthesized_demand(network, output_dir='tests/tmp')


def test_loading_synthesized_zones_demand():
    network = read_network(input_dir='tests/fixtures')

    read_zones(network, input_dir='tests/tmp')
    load_demand(network, input_dir='tests/tmp', filename='demand.csv')

    # clean up
    remove('tests/fixtures/agent.csv')
    remove('tests/fixtures/link_performance.csv')
    # remove('tests/fixtures/log_main.txt')
    rmtree('tmp')