import json as _json

def _is_hanchan_log(log):
    if not log or not isinstance(log, list) or len(log) == 0:
        return False
    first = log[0]
    return isinstance(first, list) and len(first) > 0 and isinstance(first[0], list)

def _format_single_log(log, depth):
    """单局 log 格式化：前4数组合并为一行，后续每个数组紧凑成一行"""
    indent = "  " * depth
    if not log:
        return indent + "[]"
    lines = []
    lines.append(indent + "[")
    # 前4个数组：全部紧凑拼接在一行
    first_four = ", ".join(
        _json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        for item in log[:4]
    )
    if log[:4]:
        comma = "," if len(log) > 4 else ""
        lines.append(indent + "  " + first_four + comma)
    # 第5个起：每个数组独立紧凑一行
    for i in range(4, len(log)):
        compact = _json.dumps(log[i], ensure_ascii=False, separators=(",", ":"))
        comma = "," if i < len(log) - 1 else ""
        lines.append(indent + "  " + compact + comma)
    lines.append(indent + "]")
    return "\n".join(lines)

def _format_value(val, depth):
    indent = "  " * depth
    if isinstance(val, dict):
        items = []
        for k, v in val.items():
            if k == "log":
                formatted_v = _format_log(v, depth + 1)
            else:
                formatted_v = _format_value(v, depth + 1)
            key_str = _json.dumps(k, ensure_ascii=False)
            items.append(indent + "  " + key_str + ": " + formatted_v.lstrip())
        return "{\n" + ",\n".join(items) + "\n" + indent + "}"
    elif isinstance(val, list):
        if not val:
            return "[]"
        compact = _json.dumps(val, ensure_ascii=False)
        if len(compact) <= 60:
            return compact
        items = []
        for item in val:
            items.append(_format_value(item, depth + 1))
        return "[\n" + ",\n".join(items) + "\n" + indent + "]"
    else:
        return _json.dumps(val, ensure_ascii=False)

def _format_log(log, depth):
    indent = "  " * depth
    if not log:
        return indent + "[]"
    if _is_hanchan_log(log):
        parts = []
        for i, round_data in enumerate(log):
            parts.append(_format_single_log(round_data, depth + 1))
        return indent + "[\n" + ",\n".join(parts) + "\n" + indent + "]"
    else:
        return _format_single_log(log, depth)

def format_mahjong_json(data):
    return _format_value(data, 0)