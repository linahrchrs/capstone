def parse_temp(line):
    try:
        if "TEMP:" in line:
            value = float(line.strip().split(":")[1])
            return {"temp": value}
        return None
    except:
        return None
