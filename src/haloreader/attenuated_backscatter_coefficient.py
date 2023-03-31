import logging

import numpy as np
from scipy import constants

from haloreader.type_guards import is_ndarray
from haloreader.variable import Variable

log = logging.getLogger(__name__)


def compute_beta(intensity: Variable, range_: Variable, focus: Variable) -> Variable:
    # pylint: disable=invalid-name
    if not is_ndarray(intensity.data):
        raise TypeError
    if not is_ndarray(range_.data):
        raise TypeError

    _ = 1  # PLACEHOLDER
    r = range_.data
    h = constants.Planck  # plancs_constant
    eta = _  # detector_quantum_efficiency
    c = constants.speed_of_light
    E = 1e-5  # beam_energy
    nu = _  # optical_frequency
    B = 5e7  # receiver_bandwidth
    A_e = compute_effective_receiver_energy(range_, focus)
    snr = intensity.data - 1
    # ref: https://doi.org/10.5194/amt-13-2849-2020
    beta = 2 * h * nu * B * r**2 * snr / (eta * c * E * A_e)
    return Variable(
        name="beta",
        long_name="Attenuated backscatter coefficient",
        comment="Computed using placeholder values. Do not use this variable",
        units="m-1 sr-1",
        dimensions=intensity.dimensions,
        data=beta,
    )


def compute_effective_receiver_energy(range_: Variable, focus: Variable) -> np.ndarray:
    # pylint: disable=invalid-name
    if not is_ndarray(range_.data):
        raise TypeError
    log.warning(
        "Using placeholder values from https://doi.org/10.5194/amt-13-2849-2020"
    )
    r = range_.data
    D = 25e-3  # effective_diameter_of_gaussian_beam
    f = focus.data  # effective_focal_length
    lambda_ = 1.5e-6  # laser_wavelength
    return (
        np.pi
        * D**2
        / (4 * (1 + (np.pi * D**2 / (4 * lambda_ * r)) ** 2 * (1 - r / f) ** 2))
    )
