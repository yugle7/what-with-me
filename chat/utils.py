import re
from datetime import timedelta
from cityhash import CityHash64


def get_id(a, b):
    return CityHash64(str(a) + " " + str(b).lower().strip())


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


suffixes = [
    "ями",
    "ами",
    "ими",
    "ыми",
    "ому",
    "ойю",
    "ого",
    "ему",
    "его",
    "або",
    "яя",
    "ях",
    "ям",
    "юю",
    "ых",
    "ым",
    "ый",
    "ий",
    "ые",
    "ую",
    "ом",
    "ой",
    "ое",
    "ов",
    "об",
    "их",
    "им",
    "ие",
    "ем",
    "ем",
    "ем",
    "ей",
    "ее",
    "ев",
    "ая",
    "ах",
    "ам",
    "я",
    "ь",
    "ю",
    "ы",
    "у",
    "о",
    "и",
    "е",
    "а",
]


def stem(word):
    if len(word) <= 3:
        return word
    if word.endswith("ек"):
        return word[-2:] + "к"
    for suffix in suffixes:
        if word.endswith(suffix):
            n = len(suffix)
            return word if len(word) - n <= 2 else word[:-n]
    return word


def get_hash_ids(user_id, what, name):
    name = name.lower().replace("ё", "е").strip()
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
    weights = {what: 0 for what in whats}
    for item in items:
        item["results"] = []
        for what, hash_ids in item.pop("hash_ids"):
            for i, hash_id in enumerate(hash_ids):
                if hash_id in data_ids:
                    weight = 1 - i / len(hash_ids)
                    item["results"].append((weight, what, data_ids[hash_id]))
                    weights[what] += weight
                    break

    return {what: weight / len(data_ids) for what, weight in weights.items()}


def add_data_ids(weights, items):
    dst = []
    for item in items:
        results = item.pop("results")
        if results:
            results = [
                (weight + weights[what], what, data_id)
                for weight, what, data_id in results
            ]
            item["weight"], item["what"], item["data_id"] = max(results)
            dst.append(item["data_id"])
    return tuple(set(dst))


def to_item(created, text):
    lines = text.split("\n")
    when = get_time(created, lines[0])
    if when != created:
        lines = lines[1:]
    return {"when": when, "items": [get_item(l) for l in lines], "whats": ["food"]}


def as_item(item):
    result = item.get("result")
    return {
        "name": result["name"] if result else item["name"],
        "value": item["value"],
        "unit": item["unit"],
    }


def get_item(text):
    text = text.strip()
    m = re.fullmatch(r"(.*?)[ -]+([.,\d]+) ?(\D+)[.аиуы]?(ов)?", text)
    if m:
        return {
            "name": m[1].strip(),
            "value": float(m[2].replace(",", ".")),
            "unit": unit.get(m[3].strip()),
        }
    m = re.fullmatch(r"(.*?)[ -]+([.,\d]+)", text)
    if m:
        return {
            "name": m[1].strip(),
            "value": float(m[2].replace(",", ".")),
            "unit": "шт",
        }
    m = re.fullmatch(r"(.*?) - (\D+)", text)
    if m:
        return {
            "name": m[1].strip(),
            "value": 1,
            "unit": m[2].strip(),
        }
    return {
        "name": text.strip(),
        "value": 1,
        "unit": "шт",
    }


unit = {
    "гр": "гр",
    "г": "гр",
    "грам": "гр",
    "грамм": "гр",
    "кг": "кг",
    "мин": "мин",
    "час": "час",
    "минут": "мин",
    "шт": "шт",
    "штук": "шт",
    "шаг": "шг",
    "тб": "тб",
    "таблетк": "тб",
    "л": "л",
    "литр": "л",
    "мл": "мл",
}
