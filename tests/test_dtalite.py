from os import chdir

from path4gmns.dtaapi import perform_network_assignment_DTALite, run_DTALite


def test_dtalite_link_ue():
    chdir('tests/fixtures')

    mode = 0
    column_gen_num = 20
    column_update_num = 20
    perform_network_assignment_DTALite(mode, column_gen_num, column_update_num)

    chdir('../..')


def test_dtalite_path_ue():
    chdir('tests/fixtures')

    mode = 1
    column_gen_num = 20
    column_update_num = 20
    perform_network_assignment_DTALite(mode, column_gen_num, column_update_num)

    chdir('../..')


def test_dtalite_odme():
    chdir('tests/fixtures')

    mode = 2
    column_gen_num = 20
    column_update_num = 20
    perform_network_assignment_DTALite(mode, column_gen_num, column_update_num)

    chdir('../..')


def test_dtalite_simulation():
    chdir('tests/fixtures')

    mode = 3
    column_gen_num = 20
    column_update_num = 20
    perform_network_assignment_DTALite(mode, column_gen_num, column_update_num)

    chdir('../..')


def test_multimodal_dtalite():
    run_DTALite()