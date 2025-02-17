from os import chdir, getcwd

from path4gmns.dtaapi import perform_network_assignment_DTALite


ORIG_DIR = getcwd()


def test_classic_dtalite(sample_data_dir, mode = 1):
    chdir(sample_data_dir)

    column_gen_num = 20
    column_update_num = 20
    perform_network_assignment_DTALite(mode, column_gen_num, column_update_num)

    chdir(ORIG_DIR)


# disable it from now on (10/16/24) as run_DTALite() requires a different
# settings.yml
# def test_multimodal_dtalite(sample_data_dir):
#     chdir(sample_data_dir)

#     run_DTALite()

#     chdir(ORIG_DIR)