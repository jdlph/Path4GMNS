import pytest

from os import getcwd, chdir
from os.path import join
from shutil import copytree

from path4gmns.utils import download_sample_datasets


ORIG_CWD = getcwd()
SRC_DATA_DIR = join(ORIG_CWD, 'data/Chicago_Sketch')


@pytest.fixture(scope="session")
def sample_data_dir(tmp_path_factory):
    """ create a temporary directory with sample dataset

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
def sample_dtalite_data_dir(tmp_path_factory):
    """ create a temporary directory with sample dataset downloaded from DTALiteMM

    https://github.com/asu-trans-ai-lab/DTALite/tree/feature/multimodal/data
    """
    tmp_dir = tmp_path_factory.mktemp('dtalite')
    chdir(tmp_dir)
    download_sample_datasets('DTALite')
    chdir(ORIG_CWD)
    yield str(tmp_dir)


@pytest.fixture(scope="session")
def tmp_output_dir(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("output")
    yield str(tmp_dir)
