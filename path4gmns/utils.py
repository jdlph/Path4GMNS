import os
import threading
from datetime import timedelta


# for precheck on connectivity of each OD pair
# 0: isolated, has neither outgoing links nor incoming links
# 1: has at least one outgoing link
# 2: has at least one incoming link
# 3: has both outgoing and incoming links
_zone_degrees = {}


class InvalidRecord(Exception):
    """a custom exception for invalid input from parsing a csv file"""
    pass


def _update_orig_zone(oz_id):
    if oz_id not in _zone_degrees:
        _zone_degrees[oz_id] = 1
    elif _zone_degrees[oz_id] == 2:
        _zone_degrees[oz_id] = 3


def _update_dest_zone(dz_id):
    if dz_id not in _zone_degrees:
        _zone_degrees[dz_id] = 2
    elif _zone_degrees[dz_id] == 1:
        _zone_degrees[dz_id] = 3


def _are_od_connected(oz_id, dz_id):
    connected = True

    # at least one node in O must have outgoing links
    if oz_id not in _zone_degrees or _zone_degrees[oz_id] == 2:
        connected = False
        print(f'WARNING! {oz_id} has no outgoing links to route volume '
              f'between OD: {oz_id} --> {dz_id}')

    # at least one node in D must have incoming links
    if dz_id not in _zone_degrees or _zone_degrees[dz_id] == 1:
        if connected:
            connected = False
        print(f'WARNING! {dz_id} has no incoming links to route volume '
              f'between OD: {oz_id} --> {dz_id}')

    return connected


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
    except ImportError:
        print('please print requests to proceed downloading!!')

    try:
        r = requests.get(url)
        r.raise_for_status()
        with open(loc_dir+filename, 'wb') as f:
            f.write(r.content)
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
            t = threading.Thread(
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
    url = 'https://raw.githubusercontent.com/jdlph/Path4GMNS/dev/tests/settings.yml'
    filename = 'settings.yml'
    loc_dir = './'

    _download_url(url, filename, loc_dir)

    print('downloading completes')
    print(f'check {os.getcwd()} for downloaded settings.yml')