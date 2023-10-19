import numpy as np
from sklearn.cluster import KMeans

from haloreader.exceptions import SuspiciousResult, UnexpectedInput
from haloreader.variable import Variable


def compute_wind(
    time: Variable,
    range_: Variable,
    elevation: Variable,
    azimuth: Variable,
    radial_velocity: Variable,
) -> dict[str, Variable]:
    """
    Parameters
    ----------
    elevation
        Elevation from horizontal in degrees

    azimuth
        Azimuth from North
    """

    # TODO: Check the component directions!! There is probably something shady

    timediff = np.diff(time.data).reshape(-1, 1)
    kmeans = KMeans(n_clusters=2, n_init="auto").fit(timediff)
    centers = kmeans.cluster_centers_.flatten()
    scanstep_timediff = centers[np.argmin(centers)]
    if 0.1 > scanstep_timediff or 30 < scanstep_timediff:
        raise SuspiciousResult("Unexpected time difference between scan steps")
    scanstep_timediff_upperbound = 2 * scanstep_timediff
    scan_indeces = -1 * np.ones_like(time.data, dtype=int)
    scan_indeces[0] = 0
    scan_index = 0
    for i, (t_prev, t) in enumerate(zip(time.data[:-1], time.data[1:]), start=1):
        if t - t_prev > scanstep_timediff_upperbound:
            scan_index += 1
        scan_indeces[i] = scan_index

    nscans = len(set(scan_indeces))
    wind_time_ = []
    wind_elevation_ = []
    wind_components_ = []

    if len(elevation.data) == 0 or (not np.allclose(elevation.data, elevation.data[0])):
        raise UnexpectedInput

    for j in range(nscans):
        pick_scan = scan_indeces == j
        time_ = time.data[pick_scan]
        wind_time_.append(np.median(time_))
        elevation_ = elevation.data[pick_scan]
        azimuth_ = azimuth.data[pick_scan]
        radial_velocity_ = radial_velocity.data[pick_scan]
        wind_components_.append(
            _compute_wind_components(elevation_, azimuth_, radial_velocity_)[
                np.newaxis, :, :
            ]
        )
        wind_elevation_.append(elevation_[0])
    wind_components = np.concatenate(wind_components_)
    wind_time = np.array(wind_time_)
    wind_elevation = np.array(wind_elevation_)
    horizontal_wind_speed = np.sqrt(
        wind_components[:, :, 0] ** 2 + wind_components[:, :, 1] ** 2
    )
    horizontal_wind_direction = np.arctan2(
        wind_components[:, :, 0], wind_components[:, :, 1]
    )
    horizontal_wind_direction[horizontal_wind_direction < 0] += 2 * np.pi
    height = range_.data * np.sin(np.deg2rad(elevation.data[0]))
    return {
        "time": Variable(
            name=time.name,
            long_name=time.long_name,
            calendar=time.calendar,
            units=time.units,
            dimensions=time.dimensions,
            data=wind_time,
        ),
        "height": Variable(
            name="height",
            long_name="Height above instrument",
            dimensions=range_.dimensions,
            units=range_.units,
            data=height,
        ),
        "elevation": Variable(name="elevation", data=wind_elevation),
        "meridional_wind": Variable(
            name="meridional_wind",
            dimensions=radial_velocity.dimensions,
            units=radial_velocity.units,
            data=wind_components[:, :, 1],
        ),
        "zonal_wind": Variable(
            name="zonal_wind",
            dimensions=radial_velocity.dimensions,
            units=radial_velocity.units,
            data=wind_components[:, :, 0],
        ),
        "vertical_wind": Variable(
            name="vertical_wind",
            dimensions=radial_velocity.dimensions,
            units=radial_velocity.units,
            data=wind_components[:, :, 2],
        ),
        "horizontal_wind_speed": Variable(
            name="horizontal_wind_speed",
            dimensions=radial_velocity.dimensions,
            units=radial_velocity.units,
            data=horizontal_wind_speed,
        ),
        "horizontal_wind_direction": Variable(
            name="horizontal_wind_direction",
            dimensions=radial_velocity.dimensions,
            units="degrees",
            data=np.degrees(horizontal_wind_direction),
        ),
    }


def _compute_wind_components(
    elevation: np.ndarray, azimuth: np.ndarray, radial_velocity: np.ndarray
):
    _elevation = np.deg2rad(elevation)
    _azimuth = np.deg2rad(azimuth)
    cos_elevation = np.cos(_elevation)
    A = np.hstack(
        (
            (np.sin(_azimuth) * cos_elevation).reshape(-1, 1),
            (np.cos(_azimuth) * cos_elevation).reshape(-1, 1),
            (np.sin(_elevation)).reshape(-1, 1),
        )
    )
    A_inv = np.linalg.pinv(A)
    return (A_inv @ radial_velocity).T
