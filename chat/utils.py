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


def to_text(data):
    when = data["when"].strftime("`%d.%m %H:%M`")
    items = [
        f'{item["name"]} - {str(item["value"]).removesuffix(".0")} {item["unit"]}'
        for item in data["items"]
    ]
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


def get_hash_ids(user_id, what, name):
    names = [name]

    words = re.sub(r"[^a-zа-я0-9 ]", " ", name).split()
    names.append(" ".join(words))
    words = [stem(word) for word in words]
    names.append(" ".join(words))
    names.append(" ".join(sorted(words)))

    for name in names:
        yield CityHash64(f"{user_id} {what} {name}")
        yield CityHash64(f"{what} {name}")


def add_hash_ids(user_id, whats, items):
    dst = []
    for item in items:
        item["hash_ids"] = []
        for what in whats:
            hash_ids = list(get_hash_ids(user_id, what, item["name"]))
            item["hash_ids"].append((what, hash_ids))
            dst += hash_ids
    return tuple(set(dst))


def get_weights(whats, items, data_ids):
    dst = {what: 0 for what in whats}
    for item in items:
        item["results"] = []
        for what, hash_ids in item.pop("hash_ids"):
            for i, hash_id in enumerate(hash_ids):
                if hash_id in data_ids:
                    weight = 1 - i / len(hash_ids)
                    item["results"].append((weight, what, data_ids[hash_id]))
                    dst[what] += weight
                    break

    return {what: weight / len(data_ids) for what, weight in dst.items()}


def add_data_ids(weights, items):
    dst = []
    for item in items:
        results = item.pop("results")
        if results:
            results = [
                (weight + weights[what], what, result_id)
                for weight, what, result_id in results
            ]
            item["weight"], item["what"], item["data_id"] = max(results)
            dst.append(item["data_id"])
    return tuple(set(dst))


def to_item(created, text):
    lines = text.lower().replace("ё", "е").split("\n")
    lines = [l.strip() for l in lines]
    when = get_time(created, lines[0])
    if when != created:
        lines = lines[1:]
    return {"when": when, "whats": [0], "items": [get_item(l) for l in lines]}


def as_item(item):
    names = item.get("names")
    return {
        "name": names[0] if names else item["name"],
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

    unit = UNIT.get(unit, '')
    return {"name": name, "value": value, "unit": unit}
