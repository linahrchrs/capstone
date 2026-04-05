def parse_emg(line):
    try:
        raw, env, state = line.split(",")
        return int(raw), int(env), int(state)
    except:
        return None
