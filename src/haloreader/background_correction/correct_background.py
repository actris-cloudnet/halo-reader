import logging
from pdb import set_trace as db

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.signal import medfilt2d
from sklearn import datasets, linear_model

from haloboard.writer import Writer
from haloreader.halo import Halo, HaloBg
from haloreader.variable import Variable


def threshold_cloudmask(
    intensity: Variable,
    raw_threshold: float = 1.008,
    median_filter_threshold: float = 1.003,
    gaussian_threshold: float = 0.15,
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


def snr_fit_fast(intensity: Variable, cloudmask: np.ndarray, ax=None) -> Variable:
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
        name="intensity_corrected_step2_fast",
        long_name="snr fit corrected intensity",
        data=intensity_corrected,
    )


def snr_fit(intensity: Variable, mask: np.ndarray) -> Variable:
    _range = np.arange(len(intensity.data[0]))
    writer = Writer()
    intensity_corrected = intensity.data.copy()
    N = len(intensity.data)
    for i, (profile, _mask) in enumerate(zip(intensity.data, np.logical_not(mask))):
        lr = linear_model.LinearRegression()
        huber = linear_model.HuberRegressor(
            epsilon=1.35, max_iter=1000, alpha=0.0001, tol=1e-03
        )
        _mask[:3] = False
        X = _range[_mask][:, np.newaxis]
        y = profile[_mask]
        # huber.fit(X, y)
        # intensity_corrected[i] /= huber.predict(_range[:, np.newaxis])
        lr.fit(X, y)
        intensity_corrected[i] /= lr.predict(_range[:, np.newaxis])
    return Variable.like(
        intensity,
        name="intensity_corrected_step2",
        long_name="snr fit corrected intensity",
        data=intensity_corrected,
    )


def correct_background(
    halo: Halo, halobg: HaloBg, p_amp: Variable, fit_info: dict
) -> Variable:
    if not (
        isinstance(halo.intensity.data, np.ndarray)
        and isinstance(halo.time.data, np.ndarray)
        and isinstance(halobg.background.data, np.ndarray)
        and isinstance(halobg.time.data, np.ndarray)
        and isinstance(p_amp.data, np.ndarray)
    ):
        raise TypeError
    nscale = halobg.background.data.sum(axis=1)
    _p_amp_scaled = nscale[:, np.newaxis] * p_amp.data[np.newaxis, :]
    background_shifted = Variable.like(
        halobg.background,
        data=halobg.background.data - _p_amp_scaled,
    )
    _background_fit = _linear_fit(background_shifted)
    residual = background_shifted.data - _background_fit.data
    if "residuals" not in fit_info:
        fit_info["residuals"] = residual
    else:
        fit_info["residuals"] = np.concatenate(
            (fit_info["residuals"], residual), axis=0
        )
    i2b = _previous_measurement_map(halo.time.data, halobg.time.data)
    bg_mask = np.not_equal(i2b, None)
    if not np.all(bg_mask):
        raise ValueError(
            "Could not find matching background measurement "
            "for all the intensity profiles"
        )
    i2b = i2b[bg_mask].astype(int)
    p_amp_scaled = _p_amp_scaled[i2b]
    intensity = Variable.like(halo.intensity, data=halo.intensity.data[bg_mask])
    background = Variable.like(halobg.background, data=halobg.background.data[i2b])
    if not isinstance(_background_fit.data, np.ndarray):
        raise TypeError
    background_fit = Variable.like(_background_fit, data=_background_fit.data[i2b])
    if not (
        isinstance(background.data, np.ndarray)
        and isinstance(intensity.data, np.ndarray)
    ):
        raise TypeError
    return Variable.like(
        intensity,
        name="intensity_corrected_step1",
        data=intensity.data * background.data / (p_amp_scaled + background_fit.data),
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
    return np.array(c)
