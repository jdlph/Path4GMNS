from os import chdir, getcwd, mkdir
from os.path import isdir, join
from shutil import rmtree


from path4gmns.utils import download_sample_data_sets, load_demand, \
                            output_synthesized_demand, output_zones, \
                            read_network, read_zones

from path4gmns.zonesyn import network_to_zones


def test_download_sample_data_sets(tmp_output_dir):
    orig_dir = getcwd()
    tmp_dir = join(tmp_output_dir, 'data')
    if not isdir(tmp_dir):
        mkdir(tmp_dir)

    chdir(tmp_dir)
    download_sample_data_sets()

    chdir(orig_dir)


def test_data_synthesis(sample_data_dir, tmp_output_dir):
    network = read_network(input_dir=sample_data_dir)
    network_to_zones(network)

    output_zones(network, output_dir=tmp_output_dir)
    output_synthesized_demand(network, output_dir=tmp_output_dir)


def test_loading_synthesized_data(sample_data_dir, tmp_output_dir):
    network = read_network(input_dir=sample_data_dir)

    read_zones(network, input_dir=tmp_output_dir)
    load_demand(network, input_dir=tmp_output_dir, filename='demand.csv')