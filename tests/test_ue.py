from path4gmns.colgen import perform_column_generation
from path4gmns.utils import load_columns, output_columns,\
                            output_link_performance, read_network


def test_column_generation_py():
    network = read_network(load_demand=True, input_dir='tests/fixtures')

    column_gen_num = 10
    column_update_num = 10
    perform_column_generation(column_gen_num, column_update_num, network)

    # use output_columns(network, False) to exclude geometry info in the output file,
    output_columns(network, output_dir='tests/tmp')
    output_link_performance(network, output_dir='tests/tmp')


def test_loading_columns():
    network = read_network(input_dir='tests/fixtures')
    load_columns(network, input_dir='tests/tmp')

    column_gen_num = 0
    column_update_num = 10
    perform_column_generation(column_gen_num, column_update_num, network)

    output_columns(network, output_dir='tests/tmp')
    output_link_performance(network, output_dir='tests/tmp')