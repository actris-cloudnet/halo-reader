from pdb import set_trace as db

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.signal import medfilt2d

from haloreader.variable import Variable


def background_measurement_correction(time, intensity, time_bg, bg, p_amp):
    intensity_index2bg_index = _previous_measurement_map(time.data, time_bg.data)
    relevant_bg_indeces = sorted(list(set(intensity_index2bg_index)))
    relevant_bg_indeces_map = {v: i for i, v in enumerate(relevant_bg_indeces)}
    intensity_index2relevant_bg_index = np.array(
        [relevant_bg_indeces_map[i] for i in intensity_index2bg_index]
    )
    bg_relevant = bg.take(relevant_bg_indeces)
    p_amp_denormalized = (
        bg_relevant.data.sum(axis=1)[:, np.newaxis] * p_amp.data[np.newaxis, :]
    )
    background_p_amp_removed = Variable.like(
        bg_relevant,
        long_name="p_amp removed background",
        data=bg_relevant.data - p_amp_denormalized,
    )
    bg_relevant_fit = _linear_fit(background_p_amp_removed)
    return Variable.like(
        intensity,
        name="intensity",
        standard_name = "intensity",
        comment="background measurement corrected intensity",
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


def threshold_cloudmask(
    intensity: Variable,
    raw_threshold: float = 1.008,
    median_filter_threshold: float = 1.002,
    gaussian_threshold: float = 0.02,
) -> np.ndarray:
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
    return raw_or_med_mask | gaussian_mask

def snr_correction(intensity: Variable, cloudmask: np.ndarray) -> Variable:
    _mask = cloudmask.copy()
    _mask[:, :3] = True  # ignore first three gates
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
    return Variable.like(
        intensity,
        name="intensity",
        comment = "noise corrected intensity with signal mask",
        data=intensity_corrected,
    )
