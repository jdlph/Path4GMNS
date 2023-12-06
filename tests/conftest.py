import os
import pytest
from shutil import copytree


SRC_DATA_DIR = 'data/Chicago_Sketch'


@pytest.fixture(scope="module")
def tmp_cwd(tmp_path, subdir):
    d = os.path.join(tmp_path, subdir)
    d.mkdir()
    return d


@pytest.fixture(autouse=True)
def cleanup(tmp_path):
    for tmp_file in tmp_path.iterdir():
        if tmp_file.isfile():
            yield
            os.remove(tmp_file)


# @pytest.fixture(scope="module")
def copy_files(dest_dir):
    copytree(SRC_DATA_DIR, dest_dir)