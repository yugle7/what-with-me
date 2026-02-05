from cityhash import CityHash64

import re

from const import *


def stem(word):
    if len(word) <= 3:
        return word
    if word.endswith("ек"):
        return word[-2:] + "к"
    for suffix in SUFFIX:
        if word.endswith(suffix):
            n = len(suffix)
            return word if len(word) - n <= 2 else word[:-n]
    return word


def get_hash_ids(what, name):
    names = [name]

    words = re.sub(r"[^a-zа-я0-9 ]", " ", name).split()
    names.append(" ".join(words))
    words = [stem(word) for word in words]
    names.append(" ".join(words))
    names.append(" ".join(sorted(words)))

    return [CityHash64(f"{what} {name}") for name in names]


def add_hash_ids(what, items):
    dst = []
    for item in items:
        if "data" in item:
            continue
        item["hash_ids"] = list(get_hash_ids(what, item["name"]))
        dst += item["hash_ids"]
    return tuple(set(dst))


def add_data_ids(items, data_ids):
    dst = []
    for item in items:
        if "data" in item:
            continue
        for hash_id in item.pop("hash_ids"):
            if hash_id in data_ids:
                item["data_id"] = data_ids[hash_id]
                dst.append(data_ids[hash_id])
                break
    return tuple(set(dst))


def to_item(text):
    lines = text.lower().replace("ё", "е").split("\n")
    lines = [l.strip() for l in lines]
    return {"name": lines[0], "items": [get_item(l) for l in lines[1:]]}


def as_item(item):
    return {
        "name": item["name"],
        "value": item["value"],
        "unit": item["unit"]
    }


def get_item(name):
    value = 1
    unit = ""

    m = re.fullmatch(r"(.*?)[ -]+([.,\d]+) ?(\D+)[.аиуы]?(ов)?( ложка)?", name)
    if m:
        name = m[1].strip()
        value = float(m[2].replace(",", "."))
        unit = m[3].strip()
    else:
        m = re.fullmatch(r"(.*?)[ -]+([.,\d]+)", name)
        if m:
            name = m[1].strip()
            value = float(m[2].replace(",", "."))
        else:
            m = re.fullmatch(r"(.*?) - (\D+)", name)
            if m:
                name = m[1].strip()
                unit = m[2].strip()

    unit = UNIT.get(unit)
    return {"name": name, "value": value, "unit": unit}
