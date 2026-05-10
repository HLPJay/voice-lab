def seconds_to_srt_time(value: float) -> str:
    milliseconds = int(round(value * 1000))
    hours, rem = divmod(milliseconds, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def timeline_to_srt(timeline: list[dict]) -> str:
    chunks = []
    for index, item in enumerate(timeline, start=1):
        start = seconds_to_srt_time(float(item.get("start", 0)))
        end = seconds_to_srt_time(float(item.get("end", 0)))
        text = item.get("text", "")
        chunks.append(f"{index}\n{start} --> {end}\n{text}\n")
    return "\n".join(chunks)
