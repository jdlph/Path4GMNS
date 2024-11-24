from path4gmns.colgen import find_ue
from path4gmns.io import load_columns, output_columns,\
                         output_link_performance, read_demand, read_network


def test_finding_ue(sample_data_dir, tmp_output_dir):
    network = read_network(input_dir=sample_data_dir)
    read_demand(network, input_dir=sample_data_dir)

    column_gen_num = 10
    column_update_num = 10
    find_ue(network, column_gen_num, column_update_num)

    # use output_columns(network, False) to exclude geometry info in the output file
    output_columns(network, output_dir=tmp_output_dir)
    output_link_performance(network, output_dir=tmp_output_dir)


def test_loading_columns(sample_data_dir, tmp_output_dir):
    network = read_network(input_dir=sample_data_dir)
    load_columns(network, input_dir=tmp_output_dir)

    column_gen_num = 0
    column_update_num = 10
    find_ue(network, column_gen_num, column_update_num)

    output_columns(network, output_dir=tmp_output_dir)
    output_link_performance(network, output_dir=tmp_output_dir)


def test_mixed_invoking1(sample_data_dir, tmp_output_dir):
    """ test resolution on issue #51 (https://github.com/jdlph/Path4GMNS/issues/51)
    """
    network = read_network(input_dir=sample_data_dir)
    read_demand(network, input_dir=sample_data_dir)

    # invoke find_shortest_path() before find_ue()
    network.find_shortest_path(1, 2)

    column_gen_num = 5
    column_update_num = 5
    find_ue(network, column_gen_num, column_update_num)

    # use output_columns(network, False) to exclude geometry info in the output file
    output_columns(network, output_dir=tmp_output_dir)
    output_link_performance(network, output_dir=tmp_output_dir)


def test_mixed_invoking2(sample_data_dir, tmp_output_dir):
    """ test resolution on issue #51 (https://github.com/jdlph/Path4GMNS/issues/51)
    """
    network = read_network(input_dir=sample_data_dir)
    read_demand(network, input_dir=sample_data_dir)

    column_gen_num = 5
    column_update_num = 5
    find_ue(network, column_gen_num, column_update_num)

    # use output_columns(network, False) to exclude geometry info in the output file
    output_columns(network, output_dir=tmp_output_dir)
    output_link_performance(network, output_dir=tmp_output_dir)

    # invoke find_shortest_path() after find_ue()
    network.find_shortest_path(1, 2)