def parse_pulse(data):
    try:
        if isinstance(data, (bytes, bytearray)) and len(data) > 1:
            return data[1]
        return int(data)
    except Exception:
        return None
