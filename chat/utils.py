from cityhash import CityHash64


def get_id(a, b):
    return CityHash64(str(a) + ' ' + str(b).lower().strip())
