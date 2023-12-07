import os
import pytest
from shutil import copytree, rmtree
from os.path import join


ORIG_CWD = os.getcwd()
SRC_DATA_DIR = join(ORIG_CWD, 'data/Chicago_Sketch')


@pytest.fixture(scope="session")
def sample_data_dir(tmp_path):
    print(os.getcwd())
    
    # tmp_dir = tmp_path_factory.mktemp("data")
    
    tmp_dir = tmp_path / "data"
    copytree(SRC_DATA_DIR, tmp_dir)
    
    print(tmp_dir)

    yield tmp_dir
    
    for tmp_file in tmp_dir.iterdir():
        if tmp_file.isfile():
            yield
            os.remove(tmp_file)
            print('remove tmp input file')


@pytest.fixture(scope="session")
def tmp_output_dir(tmp_path_factory):
    print(os.getcwd())
    
    tmp_dir = tmp_path_factory.mktemp("output")
    print(tmp_dir)

    yield tmp_dir
    
    # rmtree(tmp_dir)