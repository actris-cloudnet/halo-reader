import time
from datetime import datetime


class Timer:
    def __init__(self, name: str = "timer"):
        self.name = name

    def __enter__(self):
        self.start = time.perf_counter()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        end = time.perf_counter()
        t = end - self.start
        print(f"{self.name}: {t}")


def two_column_format(key: str, vals: list, left_width: int) -> str:
    if len(vals) == 0:
        return key
    str_ = key.ljust(left_width, " ") + str(vals[0])
    for v in vals[1:]:
        str_ += "\n" + " " * left_width + str(v)
    return str_


def indent_str(str_: str, width: int) -> str:
    indented_lines = []
    for line in str_.split("\n"):
        indented_lines.append(" " * width + line)
    return "\n".join(indented_lines)


def timestamp2str(stamp: float | list[float]) -> str | list[str]:
    def _timestamp2str(stamp: float) -> str:
        return datetime.utcfromtimestamp(stamp).strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(stamp, list):
        return [_timestamp2str(s) for s in stamp]
    return _timestamp2str(stamp)
