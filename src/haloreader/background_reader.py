import re

import numpy as np

from haloreader.variable import Variable


def read_background(content: bytes) -> Variable:
    numbers = [float(number) for number in re.findall(rb"\d+\.\d{6}", content)]
    return Variable(
        name="background", data=np.array([numbers]), dimensions=("time", "range")
    )
