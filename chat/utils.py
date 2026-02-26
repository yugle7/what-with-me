from datetime import timedelta
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


def get_text(data):
    when = data["when"].strftime("`%d.%m %H:%M`")
    items = [f"{name} - `{int(value)}`" for name, value in data["items"].items()]
    return "\n".join([when] + items)


def get_time(when, text):
    if "назад" in text:
        m = re.search(r"(\d+) де?н", text)
        if m:
            when -= timedelta(days=int(m[1]))
        elif "день" in text:
            when -= timedelta(days=1)
        else:
            m = re.search(r"(\d+) ч", text)
            if m:
                when -= timedelta(hours=int(m[1]))
            m = re.search(r"(\d+) мин", text)
            if m:
                when -= timedelta(minutes=int(m[1]))
            m = re.search(r"(\d+) сек", text)
            if m:
                when -= timedelta(seconds=int(m[1]))
            return when
    elif "вчера" in text:
        when -= timedelta(days=1)
    elif "позавчера" in text:
        when -= timedelta(days=2)

    m = re.search(r"(\d+):(\d+)", text)
    if m:
        when = when.replace(hour=int(m[1]), minute=int(m[2]), second=0, microsecond=0)
    else:
        m = re.search(r"(\d+) ч", text)
        if m:
            when = when.replace(hour=int(m[1]), minute=0, second=0, microsecond=0)
        m = re.search(r"(\d+) м", text)
        if m:
            when = when.replace(minute=int(m[1]), second=0, microsecond=0)
    return when


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


def get_what(items):
    what = None
    for item in items:
        if item["unit"] == "":
            continue

        if item["unit"] in ["m", "h"]:
            t = 2
        elif item["unit"] in ["br", "10"]:
            t = 1
        else:
            t = 0

        if what is None:
            what = t
        elif what != t:
            what = None
            break

    return what or 0


def get_items(created, text):
    lines = text.lower().replace("ё", "е").split("\n")
    lines = [l.strip() for l in lines]
    when = get_time(created, lines[0])
    if when != created:
        lines = lines[1:]
    return when, [get_item(l) for l in lines]


def get_size(unit, sizes):
    if unit == "":
        unit = "piece"
    if sizes and unit in sizes:
        return sizes[unit]
    if unit == "g" or unit == "ml":
        return 1
    if unit == "mg":
        return 0.001
    if unit == "mcg":
        return 0.000001
    if unit == "l" or unit == "kg":
        return 1000
    return 1


def get_data(when, items):
    data = {"when": when}
    for i in items:
        i["value"] *= get_size(i["unit"], i.get("sizes"))

    data["items"] = {i["name"]: i["value"] for i in items}
    for i in items:
        i["value"] /= 100

    keys = ["vitamins", "nutrients", "minerals"]
    for i in items:
        for k in keys:
            if k in i:
                if k not in data:
                    data[k] = {}
                for name, value in i[k].items():
                    data[k][name] = data[k].get(name, 0) + i["value"] * value
    return data


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

    unit = UNIT.get(unit, "")
    return {"name": name, "value": value, "unit": unit}
