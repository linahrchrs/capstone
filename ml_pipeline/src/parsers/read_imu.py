def parse_imu(line):
    data = {}
    try:
        parts = line.split(',')
        for p in parts:
            k, v = p.split(':')
            data[k] = float(v)
        return data
    except:
        return None
