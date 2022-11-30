from typing import Any, TypeGuard

import numpy as np


def is_str_list(val: list[Any]) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in val)


def is_float_list(val: list[Any]) -> TypeGuard[list[float]]:
    return all(isinstance(x, float) for x in val)


def is_int_list(val: list[Any]) -> TypeGuard[list[int]]:
    return all(isinstance(x, int) for x in val)


def is_float_or_float_list(
    val: Any | list[Any],
) -> TypeGuard[float | list[float]]:
    if isinstance(val, list):
        return all(isinstance(x, float) for x in val)
    else:
        return isinstance(val, float)


def is_str_or_str_list(
    val: Any | list[Any],
) -> TypeGuard[str | list[str]]:
    if isinstance(val, list):
        return all(isinstance(x, str) for x in val)
    else:
        return isinstance(val, str)


def is_ndarray_list(val: list[Any]) -> TypeGuard[list[np.ndarray]]:
    return all(isinstance(x, np.ndarray) for x in val)
