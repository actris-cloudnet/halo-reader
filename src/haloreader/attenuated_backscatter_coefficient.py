import logging

import numpy as np
from scipy import constants

from haloreader.type_guards import is_ndarray
from haloreader.variable import Variable

log = logging.getLogger(__name__)


def compute_beta(
    intensity: Variable, range_: Variable, focus: Variable, wavelength: Variable
) -> Variable:
    # pylint: disable=invalid-name
    """
    Parameters
    ----------
    range_
        distance from the instrument
    focus
        focal length og the telescope for the transmitter and receiver
    lambda_
        laser wavelength

    Local variables
    ---------------
    eta
        detector quantum efficiency
    E
        beam energy
    nu
        optical frequency
    h
        planc's constant
    c
        speed of light
    B
        reveiver bandwidth

    References
    ----------
    Methodology for deriving the telescope focus function and
    its uncertainty for a heterodyne pulsed Doppler lidar
        authors:  Pyry Pentikäinen, Ewan James O'Connor,
            Antti Juhani Manninen, and Pablo Ortiz-Amezcua
        doi: https://doi.org/10.5194/amt-13-2849-2020
    """
    if not is_ndarray(intensity.data):
        raise TypeError
    if not is_ndarray(range_.data):
        raise TypeError
    if not isinstance(wavelength.data, float):
        raise TypeError
    if wavelength.units != "m":
        raise NotImplementedError(
            f'Expected wavelength units "m", got "{wavelength.units}".'
        )

    r = range_.data
    h = constants.Planck
    eta = 1
    c = constants.speed_of_light
    E = 1e-5
    lambda_ = wavelength.data
    nu = c / lambda_
    B = 5e7
    A_e = compute_effective_receiver_energy(range_, focus, lambda_)
    snr = intensity.data - 1
    # ref: https://doi.org/10.5194/amt-13-2849-2020
    beta = 2 * h * nu * B * r**2 * snr / (eta * c * E * A_e)
    return Variable(
        name="beta",
        long_name="attenuated backscatter coefficient",
        comment=(
            "Experimental variable. Computed using uncalibrated/placeholder values."
        ),
        units="m-1 sr-1",
        dimensions=intensity.dimensions,
        data=beta,
    )


def compute_effective_receiver_energy(
    range_: Variable, focus: Variable, lambda_: float
) -> np.ndarray:
    # pylint: disable=invalid-name
    """
    Parameters
    ----------
    range_
        distance from the instrument
    focus
        effective focal length of the telescope for the transmitter and receiver
    lambda_
        laser wavelength
    """
    if not is_ndarray(range_.data):
        raise TypeError
    log.warning(
        "Using placeholder values from https://doi.org/10.5194/amt-13-2849-2020"
    )
    r = range_.data
    D = 25e-3  # effective_diameter_of_gaussian_beam
    f = focus.data  # effective_focal_length
    return (
        np.pi
        * D**2
        / (4 * (1 + (np.pi * D**2 / (4 * lambda_ * r)) ** 2 * (1 - r / f) ** 2))
    )
