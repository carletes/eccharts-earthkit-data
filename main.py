import argparse
import logging
import os
import sys
import tempfile
import threading

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import earthkit.data

from earthkit.data import ArrayField


def init_earthkit_data():
    """Configure `earthkit-data` as it's used in eccharts services."""
    earthkit.data.settings.set(
        cache_policy="off",
        grib_field_policy="temporary",
        grib_handle_policy="persistent",
        grib_handle_cache_size=1,
        number_of_download_threads=5,
        reader_type_check_bytes=4096,
        use_grib_metadata_cache=True,
    )


def retrieve(*requests):
    """Retrieve several GRIB fields in the same way as they're retrieved in
    eccharts.

    """
    results_i = []
    threads = []
    for i, req in enumerate(requests):
        req, meta = req
        t = threading.Thread(target=_retrieve, args=(req, results_i, i, meta))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    results = []
    for _, r in sorted(results_i):
        if isinstance(r, Exception):
            # XXX By raising the first error we miss any later error.
            raise r
        results.append(r)

    if len(results) == 1:
        return results[0]
    else:
        return results


LOG = logging.getLogger()


def _retrieve(request, results, index, extract_meta):
    try:
        url = request["url"]
        offset = request["offset"]
        length = request["length"]

        p = urlparse(url)
        if p.scheme in {"http", "https"}:
            source_type = "url"
            source = url
            source_extra = {"stream": True, "read_all": True}
        elif p.scheme == "file":
            source_type = "file"
            source = p.path
            source_extra = {}
        else:
            raise Exception(f"Unsupported URL {url}")
        source_part = offset, length

        fields = earthkit.data.from_source(
            source_type, source, parts=source_part, **source_extra
        )

        if len(fields) != 1:
            raise Exception(
                f"Expected one GRIB message(s), got instead {len(fields)}: {fields}"
            )

        if extract_meta:
            field = fields[0]
            arr = field.to_numpy(flatten=True)
            meta = field.metadata().override()
            field = None
            # return field.to_numpy(flatten=True), field.metadata().override()
            results.append((index, (arr, meta)))
        else:
            results.append((index, (fields[0].to_numpy(flatten=True), None)))
            
            
        # field = fields[0]

        # # import numpy as np
        # # arr = np.ones(6599680)
        
        # arr = field.to_numpy(flatten=True)

        # # XXX We will call `override()` here to save some memory.
        # meta = field.metadata().override()
        # # meta = None
        # field = None
        # fields = None
        # # XXX This was the original attempt.
        # # meta = field.metadata()

        # results.append((index, (arr, meta)))
    except Exception as exc:
        LOG.error("Error processing %s: %s", request, exc, exc_info=True)
        results.append((index, exc))


def write(values, metadata):
    """Write a GRIB field to a file on disk in the same way as we do it on
    eccharts.

    """
    fd, fname = tempfile.mkstemp(prefix="eccharts-earthikit-data-", suffix=".grib")
    os.close(fd)

    LOG.debug("Writing results to %s", fname)

    ar = ArrayField(values, metadata)
    ar.to_target("file", fname)

    # # alternative 1
    # with earthkit.data.create_target("file", fname) as t:
    #     ar = ArrayField(values, metadata)
    #     t.write(ar)

    # alternative 2
    # with open(fname, "wb") as f:
    #     with earthkit.data.create_target("file", f) as t:
    #         ar = ArrayField(values, metadata)
    #         t.write(ar)
    


def run_macro():
    """Run a simple computation in the same way as we would do in eccharts:

    * Fetch some data.
    * Compute.
    * Write the result to disk.

    """
    grib_source = Path("tp.grib").absolute().as_uri()

    (step_0, _), (step_1, metadata) = retrieve(
        ({"url": grib_source, "offset": 0, "length": 13204588}, False),
        ({"url": grib_source, "offset": 13204588, "length": 13204588}, True),
    )

    result = step_1 - step_0

    write(result, metadata)


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--iterations",
        type=int,
        metavar="N",
        help="number of times to call mock service (default: %(default)s)",
        default=100,
    )
    args = p.parse_args()

    if args.iterations <= 0:
        p.error("Positive number of iterations needed")

    logging.basicConfig(
        format="$(asctime)s %(threadName)s %(levelname)s %(name)s %(message)s",
        level=logging.DEBUG,
    )

    init_earthkit_data()

    x = ThreadPoolExecutor(max_workers=10, thread_name_prefix="worker")
    results = []
    for _ in range(args.iterations):
        r = x.submit(run_macro)
        results.append(r)

    for r in results:
        r.result()


if __name__ == "__main__":
    sys.exit(main())