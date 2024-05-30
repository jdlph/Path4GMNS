from os.path import isfile

from path4gmns.colgen import perform_column_generation
from path4gmns.simulation import perform_simple_simulation
from path4gmns.utils import load_columns, read_network, output_agent_trajectory


def test_simulation(sample_data_dir, tmp_output_dir):
    network = read_network(input_dir=sample_data_dir)

    if isfile(tmp_output_dir + '/route_assignment.csv'):
        # bypass perform_column_generation() and call load_columns(network)
        # when there is route_assignment.csv
        load_columns(network, input_dir=tmp_output_dir)
    else:
        column_gen_num = 20
        column_update_num = 20
        perform_column_generation(column_gen_num, column_update_num, network)

    # simulation
    perform_simple_simulation(network, 'uniform')
    # simulation output
    output_agent_trajectory(network, output_dir=tmp_output_dir)