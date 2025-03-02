from os.path import isfile

from path4gmns.colgen import find_ue
from path4gmns.simulation import perform_simple_simulation
from path4gmns.io import load_columns, output_agent_trajectory, \
                         read_demand, read_network


def test_simulation(sample_data_dir, tmp_output_dir):
    network = read_network(input_dir=sample_data_dir)

    if isfile(tmp_output_dir + '/route_assignment.csv'):
        # bypass perform_column_generation() and call load_columns(network)
        # when there is route_assignment.csv
        load_columns(network, input_dir=tmp_output_dir)
    else:
        read_demand(network, input_dir=sample_data_dir)
        column_gen_num = 20
        column_upd_num = 20
        find_ue(network, column_gen_num, column_upd_num)

    # simulation
    perform_simple_simulation(network, 'uniform')
    # simulation output
    output_agent_trajectory(network, output_dir=tmp_output_dir)