from os import chdir, getcwd

from path4gmns.dtaapi import perform_network_assignment_DTALite, run_DTALite


ORIG_DIR = getcwd()


def test_dtalite_link_ue(sample_data_dir):
    chdir(sample_data_dir)

    mode = 0
    column_gen_num = 20
    column_update_num = 20
    perform_network_assignment_DTALite(mode, column_gen_num, column_update_num)

    chdir(ORIG_DIR)


def test_dtalite_path_ue(sample_data_dir):
    chdir(sample_data_dir)

    mode = 1
    column_gen_num = 20
    column_update_num = 20
    perform_network_assignment_DTALite(mode, column_gen_num, column_update_num)

    chdir(ORIG_DIR)


def test_dtalite_odme(sample_data_dir):
    chdir(sample_data_dir)

    mode = 2
    column_gen_num = 20
    column_update_num = 20
    perform_network_assignment_DTALite(mode, column_gen_num, column_update_num)

    chdir(ORIG_DIR)


def test_dtalite_simulation(sample_data_dir):
    chdir(sample_data_dir)

    mode = 3
    column_gen_num = 20
    column_update_num = 20
    perform_network_assignment_DTALite(mode, column_gen_num, column_update_num)

    chdir(ORIG_DIR)


def test_multimodal_dtalite(sample_data_dir):
    chdir(sample_data_dir)

    run_DTALite()

    chdir(ORIG_DIR)