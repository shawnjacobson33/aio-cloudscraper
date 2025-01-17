def update_attr(obj, name, new_value):
    try:
        obj[name].update(new_value)
        return obj[name]
    except (AttributeError, KeyError):
        obj[name] = {}
        obj[name].update(new_value)
        return obj[name]