import pytest

from os import getcwd
from os.path import join
from shutil import copytree


ORIG_CWD = getcwd()
SRC_DATA_DIR = join(ORIG_CWD, 'data/Chicago_Sketch')


@pytest.fixture(scope="session")
def sample_data_dir(tmp_path_factory):
    """ create a temporary directory with sample data set

    do not explicitly remove temporary folder and files but leave the removal
    to Pytest (i.e., entries older than 3 temporary directories will be removed).

    output files from DTALite would not be released and removing them will trigger
    PermissionError. A possible remedy is to use multiprocessing to handle test
    case of DTALite.
    """
    tmp_dir = tmp_path_factory.mktemp('data')
    copytree(SRC_DATA_DIR, tmp_dir, dirs_exist_ok=True)
    yield str(tmp_dir)


@pytest.fixture(scope="session")
def tmp_output_dir(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("output")
    yield str(tmp_dir)