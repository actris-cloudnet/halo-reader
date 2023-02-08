import numpy as np

from haloreader.halo import Halo, HaloBg
from haloreader.variable import Variable


def correct_background(
    halo: Halo, halobg: HaloBg, p_amp: Variable
) -> Variable:
    if not (
        isinstance(halo.intensity.data, np.ndarray)
        and isinstance(halo.time.data, np.ndarray)
        and isinstance(halobg.background.data, np.ndarray)
        and isinstance(halobg.time.data, np.ndarray)
        and isinstance(p_amp.data, np.ndarray)
    ):
        raise TypeError
    background_shifted = Variable.like(
        halobg.background, data=halobg.background.data - p_amp.data
    )
    _background_fit = _linear_fit(background_shifted)
    i2b = _previous_measurement_map(halo.time.data, halobg.time.data)
    bg_mask = i2b is None
    if not np.all(bg_mask):
        raise ValueError(
            "Could not find matching background measurement "
            "for all the intensity profiles"
        )
    i2b = i2b[bg_mask].astype(int)
    intensity = Variable.like(
        halo.intensity, data=halo.intensity.data[bg_mask]
    )
    background = Variable.like(
        halobg.background, data=halobg.background.data[i2b]
    )
    if not isinstance(_background_fit.data, np.ndarray):
        raise TypeError
    background_fit = Variable.like(
        _background_fit, data=_background_fit.data[i2b]
    )
    if not (
        isinstance(background.data, np.ndarray)
        and isinstance(intensity.data, np.ndarray)
    ):
        raise TypeError
    return Variable.like(
        intensity,
        name="intensity_corrected",
        data=intensity.data
        * background.data
        / (p_amp.data + background_fit.data),
    )


def _linear_fit(background: Variable) -> Variable:
    # pylint: disable=invalid-name
    if not isinstance(background.data, np.ndarray):
        raise TypeError
    r = 3  # ignore first three gates
    n = background.data.shape[1]
    A = np.array([np.arange(n), np.ones(n)]).T
    A_inv = np.linalg.pinv(A[r:])
    x = A_inv @ background.data.T[r:]
    bg_fit = A @ x
    return Variable(
        name="background_fit", dimensions=("time", "range"), data=bg_fit.T
    )


def _previous_measurement_map(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # pylint: disable=invalid-name
    """
    Parameters
    ----------
    a, b
        Sorted array
    Returns
    -------
    c: array
        c[i] = j where j is largest index such that b[j] <= a[i]
    """
    i = 0
    j = 0
    n_a = len(a)
    n_b = len(b)
    c: list[int | None] = [None] * n_a
    while i < n_a and j < n_b:
        if b[j] <= a[i] and (j == n_b - 1 or a[i] < b[j + 1]):
            c[i] = j
            i += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1
    return np.array(c)
