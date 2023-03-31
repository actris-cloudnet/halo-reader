import numpy as np
from scipy.ndimage import gaussian_filter  # mypy:
from scipy.signal import medfilt2d

from haloreader.type_guards import is_ndarray
from haloreader.variable import Variable


def background_measurement_correction(
    time: Variable,
    intensity: Variable,
    time_bg: Variable,
    bg: Variable,
    p_amp: Variable,
) -> Variable:
    # ref: https://doi.org/10.5194/amt-12-839-2019
    if not is_ndarray(time.data):
        raise TypeError
    if not is_ndarray(intensity.data):
        raise TypeError
    if not is_ndarray(time_bg.data):
        raise TypeError
    if not is_ndarray(bg.data):
        raise TypeError
    if not is_ndarray(p_amp.data):
        raise TypeError
    intensity_index2bg_index = _previous_measurement_map(time.data, time_bg.data)
    relevant_bg_indeces = sorted(list(set(intensity_index2bg_index)))
    relevant_bg_indeces_map = {v: i for i, v in enumerate(relevant_bg_indeces)}
    intensity_index2relevant_bg_index = np.array(
        [relevant_bg_indeces_map[i] for i in intensity_index2bg_index]
    )
    bg_relevant = bg.take(relevant_bg_indeces)
    if not is_ndarray(bg_relevant.data):
        raise TypeError
    p_amp_denormalized = (
        bg_relevant.data.sum(axis=1)[:, np.newaxis] * p_amp.data[np.newaxis, :]
    )
    background_p_amp_removed = Variable(
        name="background_p_amp_removed",
        dimensions=bg_relevant.dimensions,
        comment="p_amp removed background",
        data=bg_relevant.data - p_amp_denormalized,
    )
    bg_relevant_fit = _linear_fit(background_p_amp_removed)
    if not is_ndarray(bg_relevant_fit.data):
        raise TypeError
    return Variable(
        name="intensity",
        comment="background measurement corrected intensity",
        dimensions=intensity.dimensions,
        units=intensity.units,
        data=intensity.data
        * bg.data[intensity_index2bg_index]
        / (
            p_amp_denormalized[intensity_index2relevant_bg_index]
            + bg_relevant_fit.data[intensity_index2relevant_bg_index]
        ),
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
    return Variable(name="background_fit", dimensions=("time", "range"), data=bg_fit.T)


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
    if None in c:
        raise ValueError
    return np.array(c, dtype=int)


def threshold_signalmask(
    intensity: Variable,
    raw_threshold: float = 1.008,
    median_filter_threshold: float = 1.002,
    gaussian_threshold: float = 0.02,
) -> np.ndarray:
    """
    mask = 1, if data is signal
    mask = 0, if data is noise
    """
    if not is_ndarray(intensity.data):
        raise TypeError
    intensity_median_normalised = (
        intensity.data / np.median(intensity.data, axis=1)[:, np.newaxis]
    )
    raw_mask = intensity_median_normalised > raw_threshold
    med_mask = (
        medfilt2d(intensity_median_normalised, kernel_size=5) > median_filter_threshold
    )
    raw_or_med_mask = raw_mask | med_mask
    gaussian = gaussian_filter(raw_or_med_mask.astype(float), sigma=8, radius=16)
    gaussian_mask = np.zeros_like(raw_or_med_mask)
    gaussian_mask[gaussian > gaussian_threshold] = True
    signalmask = raw_or_med_mask | gaussian_mask
    if not is_ndarray(signalmask):
        raise TypeError
    return signalmask


def snr_correction(intensity: Variable, signalmask: np.ndarray) -> Variable:
    # pylint: disable=invalid-name
    if not is_ndarray(intensity.data):
        raise TypeError
    _mask = signalmask.copy()
    # Fit only to noise ie where signalmask is False
    _mask[:, :3] = True  # ignore first three gates since they often containt bad data
    _range = np.arange(intensity.data.shape[1], dtype=intensity.data.dtype)
    _ones = np.ones_like(_range)
    _A = np.concatenate((_range[:, np.newaxis], _ones[:, np.newaxis]), axis=1)
    A = np.repeat(_A[np.newaxis, :, :], intensity.data.shape[0], axis=0)
    A_mask = np.repeat(_mask[:, :, np.newaxis], 2, axis=2)
    A[A_mask] = 0
    A_pinv = np.linalg.pinv(A)
    _intensity = intensity.data.copy()
    _intensity[_mask] = 0
    x = A_pinv @ _intensity[:, :, np.newaxis]
    noise_fit = np.squeeze(_A[np.newaxis, :, :] @ x, axis=2)
    intensity_corrected = intensity.data.copy()
    intensity_corrected /= noise_fit
    return Variable(
        name="intensity",
        long_name="background corrected intensity",
        units=intensity.units,
        dimensions=intensity.dimensions,
        data=intensity_corrected,
    )
