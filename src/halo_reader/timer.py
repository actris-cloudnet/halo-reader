import time


class Timer:
    def __init__(self) -> None:
        self.start = time.perf_counter()

    def stop(self) -> float:
        return time.perf_counter() - self.start
