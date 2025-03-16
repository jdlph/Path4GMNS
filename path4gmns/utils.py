import os
from datetime import timedelta
from threading import Thread

from .consts import MILE_TO_METER, MPH_TO_KPH


__all__ = ['download_sample_data_sets', 'download_sample_setting_file']


class InvalidRecord(Exception):
    """a custom exception for invalid input from parsing a csv file"""
    pass


# a little bit ugly
def _convert_str_to_int(s):
    if not s:
        raise InvalidRecord

    try:
        return int(s)
    except ValueError:
        # if s is not numeric, a ValueError will be then caught
        try:
            return int(float(s))
        except ValueError:
            raise InvalidRecord
    except TypeError:
        raise InvalidRecord


def _convert_str_to_float(s):
    if not s:
        raise InvalidRecord

    try:
        return float(s)
    except (TypeError, ValueError):
        raise InvalidRecord


def _convert_boundaries(bs):
    """a helper function to facilitate read_zones()"""
    if not bs:
        raise InvalidRecord

    prefix = 'LINESTRING ('
    postfix = ')'

    try:
        b = bs.index(prefix) + len(prefix)
        e = bs.index(postfix)
    except ValueError:
        raise Exception(f'Invalid Zone Boundaries: {bs}')

    bs_ = bs[b:e]
    vs = [x for x in bs_.split(',')]

    # validation
    if len(vs) != 5:
        raise Exception(f'Invalid Zone Boundaries: {bs}')

    if vs[0] != vs[-1]:
        raise Exception(f'Invalid Zone Boundaries: {bs}')

    L, U = vs[0].split(' ')
    R, U_ = vs[1].split(' ')
    if U != U_:
        raise Exception(
            f'Invalid Zone Boundaries: inconsistent upper boundary {U}; {U_}'
        )

    R_, D = vs[2].split(' ')
    if R != R_:
        raise Exception(
            'Invalid Zone Boundaries: inconsistent right boundary {R}; {R_}'
        )

    L_, D_ = vs[3].split(' ')
    if L != L_:
        raise Exception(
            'Invalid Zone Boundaries: inconsistent left boundary {L}; {L_}'
        )

    if D != D_:
        raise Exception(
            'Invalid Zone Boundaries: inconsistent lower boundary {D}; {D_}'
        )

    U = _convert_str_to_float(U)
    D = _convert_str_to_float(D)
    L = _convert_str_to_float(L)
    R = _convert_str_to_float(R)

    return U, D, L, R


def _get_time_stamp(minute):
    """ covert minute into HH:MM:SS as string """
    s = minute * 60
    return str(timedelta(seconds=s))


def _download_url(url, filename, loc_dir):
    try:
        import requests

        r = requests.get(url)
        r.raise_for_status()
        with open(loc_dir+filename, 'wb') as f:
            f.write(r.content)
    except ImportError:
        print('please install requests to proceed downloading!!')
    except requests.HTTPError:
        print(f'file not existing: {url}')
    except requests.ConnectionError:
        raise Exception('check your connection!!!')
    except Exception as e:
        raise e


def download_sample_data_sets():
    """ download sample data sets from the Github repo

    the following data sets will be downloaded: ASU, Braess Paradox, Chicago Sketch,
    Lima Network, Sioux Falls, and Two Corridors.
    """
    url = 'https://raw.githubusercontent.com/jdlph/Path4GMNS/dev/data/'

    data_sets = [
        "ASU",
        "Braess_Paradox",
        "Chicago_Sketch",
        "Lima_Network",
        "Sioux_Falls",
        "Two_Corridor"
    ]

    files = [
        "node.csv",
        "link.csv",
        "demand.csv",
        "measurement.csv",
        "settings.csv",
        "settings.yml"
    ]

    print('downloading starts')

    # data folder under cdw
    loc_data_dir = 'data'
    if not os.path.isdir(loc_data_dir):
        os.mkdir(loc_data_dir)

    for ds in data_sets:
        web_dir = url + ds + '/'
        loc_sub_dir = os.path.join(loc_data_dir, ds) + '/'

        if not os.path.isdir(loc_sub_dir):
            os.mkdir(loc_sub_dir)

        # multi-threading
        threads = []
        for x in files:
            t = Thread(
                target=_download_url,
                args=(web_dir+x, x, loc_sub_dir)
            )
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    print('downloading completes')
    print(f'check {os.path.join(os.getcwd(), loc_data_dir)} for downloaded data sets')


def download_sample_setting_file():
    """ download the sample settings.yml from the Github repo """
    url = 'https://raw.githubusercontent.com/jdlph/Path4GMNS/master/data/Chicago_Sketch/settings.yml'
    filename = 'settings.yml'
    loc_dir = './'

    _download_url(url, filename, loc_dir)

    print('downloading completes')
    print(f'check {os.getcwd()} for downloaded settings.yml')


def get_len_unit_conversion_factor(unit):
    len_units = ['kilometer', 'km', 'meter', 'm', 'mile', 'mi']

    # length unit check
    # linear search is OK for such small lists
    if unit not in len_units:
        units = ', '.join(len_units)
        raise Exception(
            f'Invalid length unit: {unit} !'
            f' Please choose one available unit from {units}'
        )

    cf = 1
    if unit.startswith('meter') or unit == 'm':
        cf = MILE_TO_METER
    elif unit.startswith('kilometer') or unit.startswith('km'):
        cf = MPH_TO_KPH

    return cf


def get_spd_unit_conversion_factor(unit):
    spd_units = ['kmh', 'kph', 'mph']

    # speed unit check
    if unit not in spd_units:
        units = ', '.join(spd_units)
        raise Exception(
            f'Invalid speed unit: {unit} !'
            f' Please choose one available unit from {units}'
        )

    if unit.startswith('kmh') or unit.startswith('kph'):
        return MPH_TO_KPH

    return 1
