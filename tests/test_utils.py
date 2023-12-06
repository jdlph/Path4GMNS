from os import chdir, mkdir, remove
from os.path import isdir
from shutil import rmtree


from path4gmns.utils import download_sample_data_sets, load_demand, \
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


def test_data_synthesis():
    network = read_network(input_dir='tests/fixtures')
    network_to_zones(network)

    output_zones(network, output_dir='tests/tmp')
    output_synthesized_demand(network, output_dir='tests/tmp')


def test_loading_synthesized_data():
    network = read_network(input_dir='tests/fixtures')

    read_zones(network, input_dir='tests/tmp')
    load_demand(network, input_dir='tests/tmp', filename='demand.csv')

    # clean up
    remove('tests/fixtures/agent.csv')
    remove('tests/fixtures/link_performance.csv')
    # remove('tests/fixtures/log_main.txt')
    rmtree('tmp')