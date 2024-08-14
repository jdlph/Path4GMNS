from os import chdir, getcwd

from path4gmns.utils import download_sample_data_sets
from path4gmns.io import read_demand, read_network


def test_download_sample_data_sets(tmp_output_dir):
    orig_dir = getcwd()

    chdir(tmp_output_dir)
    download_sample_data_sets()

    chdir(orig_dir)


def test_data_synthesis(sample_data_dir, tmp_output_dir):
    network = read_network(input_dir=sample_data_dir)

    # try to load synthetic data if there is any. otherwise, synthesize demand
    # and zones, and output them.
    read_demand(network, use_synthetic_data = True, input_dir=tmp_output_dir)