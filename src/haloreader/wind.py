import numpy as np
from scipy.ndimage import generic_filter
from sklearn.cluster import KMeans

from haloreader.exceptions import SuspiciousResult, UnexpectedInput
from haloreader.variable import Variable


def compute_wind(
    time: Variable,
    range_: Variable,
    elevation: Variable,
    azimuth: Variable,
    radial_velocity: Variable,
    intensity: Variable,
) -> dict[str, Variable]:
    """
    Parameters
    ----------
    elevation
        Elevation from horizontal in degrees

    azimuth
        Azimuth from North
    """

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
    scan_max_intensity_ = []
    scan_rmse_ = []

    if len(elevation.data) == 0 or (
        not np.allclose(np.round(elevation.data, 1), elevation.data[0])
    ):
        raise UnexpectedInput

    for j in range(nscans):
        pick_scan = scan_indeces == j
        time_ = time.data[pick_scan]
        wind_time_.append(np.median(time_))
        elevation_ = elevation.data[pick_scan]
        azimuth_ = azimuth.data[pick_scan]
        radial_velocity_ = radial_velocity.data[pick_scan]
        intensity_ = intensity.data[pick_scan]
        scan_max_intensity_.append(
            np.max(intensity.data[pick_scan], axis=0)[np.newaxis, :]
        )
        wcomp_, rmse_ = _compute_wind_components(elevation_, azimuth_, radial_velocity_)
        wind_components_.append(wcomp_[np.newaxis, :, :])
        scan_rmse_.append(rmse_[np.newaxis, :])
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
    scan_max_intensity = np.concatenate(scan_max_intensity_)
    scan_rmse = np.concatenate(scan_rmse_)
    mask = _compute_mask(wind_components, scan_max_intensity, scan_rmse)

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
        "zonal_wind": Variable(
            name="zonal_wind",
            dimensions=radial_velocity.dimensions,
            units=radial_velocity.units,
            data=wind_components[:, :, 0],
        ),
        "meridional_wind": Variable(
            name="meridional_wind",
            dimensions=radial_velocity.dimensions,
            units=radial_velocity.units,
            data=wind_components[:, :, 1],
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
        "mask": mask,
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

    w = A_inv @ radial_velocity
    r_appr = A @ w
    rmse = np.sqrt(np.sum((r_appr - radial_velocity) ** 2, axis=0) / r_appr.shape[0])
    return w.T, rmse


def _compute_mask(comp, intensity, rmse):
    """
    Parameters
    ----------
    comp[t,r,i]: wind components
        t := time dimension
        r := range dimension
        i := component index
            i=0: zonal wind
            i=1: meridional wind
            i=0: vertical wind
    """

    def neighbour_diff(X):
        mdiff = np.max(np.abs(X - X[len(X) // 2]))
        return mdiff

    neighbour_mask = np.any(
        generic_filter(comp, neighbour_diff, size=(1, 3, 1)) > 5, axis=2
    )

    ## RMSE
    # rmse_th = 4.834278527280794
    rmse_th = 4.8
    return (rmse > rmse_th) | neighbour_mask
