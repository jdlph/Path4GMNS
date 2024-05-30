from path4gmns.colgen import perform_column_generation
from path4gmns.utils import load_columns, output_columns,\
                            output_link_performance, read_network


def test_column_generation_py(sample_data_dir, tmp_output_dir):
    network = read_network(input_dir=sample_data_dir)

    column_gen_num = 10
    column_update_num = 10
    perform_column_generation(column_gen_num, column_update_num, network)

    # use output_columns(network, False) to exclude geometry info in the output file
    output_columns(network, output_dir=tmp_output_dir)
    output_link_performance(network, output_dir=tmp_output_dir)


def test_loading_columns(sample_data_dir, tmp_output_dir):
    network = read_network(load_demand=False, input_dir=sample_data_dir)
    load_columns(network, input_dir=tmp_output_dir)

    column_gen_num = 0
    column_update_num = 10
    perform_column_generation(column_gen_num, column_update_num, network)

    output_columns(network, output_dir=tmp_output_dir)
    output_link_performance(network, output_dir=tmp_output_dir)