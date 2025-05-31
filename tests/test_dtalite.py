from os import chdir, getcwd, path

from path4gmns.dtaapi import DTALiteClassic, DTALiteMultimodal


ORIG_DIR = getcwd()


def test_classic_dtalite(sample_data_dir, mode = 1):
    chdir(sample_data_dir)

    column_gen_num = 20
    column_upd_num = 20
    DTALiteClassic(mode, column_gen_num, column_upd_num)

    chdir(ORIG_DIR)


def test_multimodal_dtalite(sample_dtalite_data_dir):
    tgt_dir = path.join(sample_dtalite_data_dir, '03_Chicago_Sketch/minimum_input')
    chdir(tgt_dir)

    DTALiteMultimodal()

    chdir(ORIG_DIR)
