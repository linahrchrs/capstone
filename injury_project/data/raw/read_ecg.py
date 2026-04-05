def parse_ecg(line):
    try:
        return int(line)
    except:
        return None
