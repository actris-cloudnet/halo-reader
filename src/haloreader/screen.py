import numpy as np
from scipy.ndimage import uniform_filter

from haloreader.type_guards import is_ndarray
from haloreader.variable import Variable


def compute_noise_screen(intensity: Variable, doppler_velocity: Variable) -> Variable:
    if not is_ndarray(intensity.data) or not is_ndarray(doppler_velocity.data):
        raise TypeError
    # kernel size and threshold values have been chosen just by
    # visually checking the output
    intensity_mean_mask = uniform_filter(intensity.data, size=(21, 3)) > 1.0025
    velocity_abs_mean_mask = (
        uniform_filter(np.abs(doppler_velocity.data), size=(21, 3)) < 2
    )
    bad_gates = np.zeros_like(intensity.data, dtype=bool)
    bad_gates[:, :3] = True
    below_one = intensity.data < 1
    return Variable(
        name="noise_screen",
        dimensions=intensity.dimensions,
        data=np.logical_not(intensity_mean_mask | velocity_abs_mean_mask)
        | bad_gates
        | below_one,
    )
