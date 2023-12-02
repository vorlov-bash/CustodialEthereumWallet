def build_map_from_list_of_dicts(list_of_dicts: list[dict], key: str) -> dict[str, dict]:
    return {item[key]: item for item in list_of_dicts}
