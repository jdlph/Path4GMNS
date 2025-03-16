import os
import ctypes
import platform
from multiprocessing import Process
from time import sleep


__all__ = ['perform_network_assignment_DTALite', 'run_DTALite']


_os = platform.system()
if _os.startswith('Windows'):
    _dtalite_dll = os.path.join(os.path.dirname(__file__), 'bin/DTALite.dll')
    _dtalitemm_dll = os.path.join(os.path.dirname(__file__), 'bin/DTALiteMM.dll')
elif _os.startswith('Linux'):
    _dtalite_dll = os.path.join(os.path.dirname(__file__), 'bin/DTALite.so')
    _dtalitemm_dll = os.path.join(os.path.dirname(__file__), 'bin/DTALiteMM.so')
elif _os.startswith('Darwin'):
    # check CPU is Intel or Apple Silicon
    if platform.machine().startswith('x86_64'):
        _dtalite_dll = os.path.join(os.path.dirname(__file__), 'bin/DTALite_x86.dylib')
        _dtalitemm_dll = os.path.join(os.path.dirname(__file__), 'bin/DTALiteMM_x86.dylib')
    else:
        _dtalite_dll = os.path.join(os.path.dirname(__file__), 'bin/DTALite_arm.dylib')
        _dtalitemm_dll = os.path.join(os.path.dirname(__file__), 'bin/DTALiteMM_arm.dylib')
else:
    raise Exception(
        'Please build the shared library compatible to your OS using source files'
    )


def _emit_log(log_file='log_main.txt'):
    with open(log_file, 'r') as fp:
        for line in fp:
            print(line)


def perform_network_assignment_DTALite(assignment_mode,
                                       column_gen_num,
                                       column_upd_num):
    """ DEPRECATED Python interface to call DTALite (precompiled as shared library)

    perform network assignment using the selected assignment mode

    WARNING
    -------
    MAKE SURE TO BACKUP route_assignment.csv and link_performance.csv if you have
    called find_ue() before. Otherwise, they will be overwritten by results
    generated by DTALite.

    Parameters
    ----------
    assignment_mode
        0: Link-based UE, only generates link performance file without agent path file

        1: Path-based UE, generates link performance file and agent path file

        2: UE + dynamic traffic assignment (DTA), generates link performance file and agent path file

        3: ODME

    column_gen_num
        number of iterations to be performed before on generating column pool

    column_upd_num
        number of iterations to be performed on optimizing column pool

    Returns
    -------
    None

    Note
    ----
    The output will depend on the selected assignment_mode.

        Link-based UE: link_performance.csv

        Path-based UE: route_assignment.csv and link_performance.csv

        UE + DTA: route_assignment.csv and link_performance.csv

    route_assignment.csv: paths/columns

    link_performance.csv: assigned volumes and other link attributes
    on each link
    """
    # make sure assignment_mode is right
    assert(assignment_mode in [0, 1, 2, 3])
    # make sure iteration numbers are both non-negative
    assert(column_gen_num>=0)
    assert(column_upd_num>=0)

    _dtalite_engine = ctypes.cdll.LoadLibrary(_dtalite_dll)
    _dtalite_engine.network_assignment.argtypes = [ctypes.c_int,
                                                   ctypes.c_int,
                                                   ctypes.c_int]

    print('This function has been deprecated, and will be removed later!'
          'Please use run_DTALite() instead!')
    print('\nDTALite run starts\n')

    if _os.startswith('Windows'):
        _dtalite_engine.network_assignment(assignment_mode,
                                           column_gen_num,
                                           column_upd_num)

        _emit_log()

        print('\nDTALite run completes\n')
        print(
            f'check link_performance.csv in {os.getcwd()} for link performance\n'
            f'check route_assignment.csv in {os.getcwd()} for unique agent paths\n'
        )
    else:
        # the following multiprocessing call does not work for Windows,
        # and there is no solution.
        # OSError: [WinError 87] The parameter is incorrect
        proc_dta = Process(
            target=_dtalite_engine.network_assignment,
            args=(assignment_mode, column_gen_num, column_upd_num,)
        )

        proc_print = Process(target=_emit_log)

        proc_dta.start()
        proc_dta.join()

        if proc_dta.exitcode is not None:
            sleep(0.1)
            proc_print.start()
            proc_print.join()
            if proc_dta.exitcode == 0:
                print('DTALite run completes!\n')
                print(
                    f'check link_performance.csv in {os.getcwd()} for link performance\n'
                    f'check route_assignment.csv in {os.getcwd()} for unique agent paths\n'
                )
            else:
                print('DTALite run terminates!')


def run_DTALite():
    """ Python interface to call the latest DTALite

    This version of DTALite includes all-new Logbook, enhanced scenario handling,
    improved I/O functionality, and so on.

    Its source code can be found at https://github.com/asu-trans-ai-lab/DTALite/tree/feature/multimodal.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Note
    ----
    It is NOT compatible with the classic DTALite (i.e., perform_network_assignment_DTALite()).

    Only use the following data set from
    https://github.com/asu-trans-ai-lab/DTALite/tree/feature/multimodal/data.

    Please run the script calling this API using your system terminal rather than
    Python console for proper logging.
    """
    _dtalitemm_engine = ctypes.cdll.LoadLibrary(_dtalitemm_dll)
    print('\nDTALite run starts\n')

    proc_dta = Process(target=_dtalitemm_engine.DTALiteAPI())
    proc_print = Process(target=_emit_log, args=('log_DTA.txt',))

    proc_dta.start()
    proc_dta.join()

    if proc_dta.exitcode is not None:
        sleep(0.1)
        proc_print.start()
        proc_print.join()
        if proc_dta.exitcode == 0:
            print('DTALite run completes!')
        else:
            print('DTALite run terminates!')