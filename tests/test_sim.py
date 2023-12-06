import os
import pytest

from conftest import copy_files

from path4gmns.colgen import perform_column_generation
from path4gmns.simulation import perform_simple_simulation
from path4gmns.utils import load_columns, read_network, output_agent_trajectory


@pytest.mark.parametrize('tmp_cwd', ['sim_py'])
def test_simulation(tmp_cwd):
    copy_files(tmp_cwd)
    network = read_network(load_demand=True, input_dir=tmp_cwd)

    if os.path.isfile('tests/fixtures/agent.csv'):
        # bypass perform_column_generation() and call load_columns(network)
        # when there is agent.csv
        load_columns(network, input_dir='tests/tmp')
    else:
        column_gen_num = 20
        column_update_num = 20
        perform_column_generation(column_gen_num, column_update_num, network)

    # simulation
    perform_simple_simulation(network, 'uniform')
    # simulation output
    output_agent_trajectory(network, output_dir='tests/tmp')