from os import chdir, getcwd, path

from path4gmns.dtaapi import perform_network_assignment_DTALite, run_DTALite


ORIG_DIR = getcwd()


def test_classic_dtalite(sample_data_dir, mode = 1):
    chdir(sample_data_dir)

    column_gen_num = 20
    column_upd_num = 20
    perform_network_assignment_DTALite(mode, column_gen_num, column_upd_num)

    chdir(ORIG_DIR)


def test_multimodal_dtalite(sample_dtalite_data_dir):
    tgt_dir = path.join(sample_dtalite_data_dir, '03_Chicago_Sketch/minimum_input')
    chdir(tgt_dir)

    run_DTALite()

    chdir(ORIG_DIR)
