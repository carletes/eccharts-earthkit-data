import logging
import sys

from pathlib import Path

import earthkit.data

from earthkit.regrid import interpolate
from earthkit.regrid.utils.caching import SETTINGS as earthkit_regrid_settings


def init_earthkit():
    """Configure `earthkit-data` and `earthkit-regrid` as they're used in eccharts services."""
    earthkit.data.settings.set(
        cache_policy="off",
        grib_field_policy="temporary",
        grib_handle_policy="temporary",
        grib_handle_cache_size=0,
        number_of_download_threads=51,
        reader_type_check_bytes=4096,
        use_grib_metadata_cache=True,
    )

    # XXX Is this the right way of configuring `earthkit-regrid`?
    earthkit_regrid_settings["cache-policy"] = "user"

    # In containers use a non-default directory for this
    # earthkit_regrid_settings["user-cache-directory"] = "/var/cache/earthkit-regrid"

    earthkit_regrid_settings["maximum-cache-size"] = None
    earthkit_regrid_settings["maximum-cache-disk-usage"] = None
    earthkit_regrid_settings["url-download-timeout"] = 30
    earthkit_regrid_settings["check-out-of-date-urls"] = False
    earthkit_regrid_settings["download-out-of-date-urls"] = False


LOG = logging.getLogger()


def main():
    logging.basicConfig(
        format="%(asctime)s %(threadName)s %(levelname)s %(name)s %(message)s",
        level=logging.INFO,
    )

    # Read the input data.
    grib_source = Path("tp.grib").absolute().as_uri()
    tp = earthkit.data.from_source("url", [grib_source, [0, 13204588]])[0]

    metadata = tp.metadata()
    in_grid = metadata.gridspec
    LOG.info("in_grid: %s", in_grid)

    tp = tp.to_numpy(flatten=False)
    LOG.info("tp shape: %s", tp.shape)

    # Regrid to [0.1, 0.1].
    out_grid = {"grid": [0.1, 0.1], "type": "regular_ll"}
    tp_regridded = interpolate(tp, in_grid=in_grid, out_grid=out_grid)
    LOG.info("tp shape (regridded): %s", tp_regridded.shape)

    # Save regridded data.
    #
    # XXX Is this the right way to write to a GRIB file?
    with earthkit.data.create_target("file", "tp-regridded.grib") as t:
        # XXX Is this the right way to override the grid in the metadata?
        metadata = metadata.override(gridspec=metadata.gridspec.override(**out_grid))
        ar = earthkit.data.ArrayField(tp_regridded, metadata)
        t.write(ar)


if __name__ == "__main__":
    sys.exit(main())
