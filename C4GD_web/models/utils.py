def select_keys(d, keys):
    for k, v in d.items():
        if k in keys:
            yield v
