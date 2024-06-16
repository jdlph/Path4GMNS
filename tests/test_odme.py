from os.path import isfile

from path4gmns.colgen import perform_column_generation
from path4gmns.odme import conduct_odme
from path4gmns.utils import load_columns, read_network, read_measurements, \
                            output_link_performance


def test_simulation(sample_data_dir, tmp_output_dir):
    network = None

    if isfile(tmp_output_dir + '/route_assignment.csv'):
        network = read_network(load_demand=False, input_dir=sample_data_dir)
        # bypass perform_column_generation() and call load_columns(network)
        # when there is route_assignment.csv
        load_columns(network, input_dir=tmp_output_dir)
    else:
        network = read_network(input_dir=sample_data_dir)
        column_gen_num = 20
        column_update_num = 20
        perform_column_generation(column_gen_num, column_update_num, network)

    # ODME
    odme_update_num = 20
    read_measurements(input_dir=sample_data_dir)
    conduct_odme(odme_update_num, network)
    # ODME output
    output_link_performance(network, mode='odme', output_dir=tmp_output_dir)