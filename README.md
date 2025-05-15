# Mock eccharts service using `earthkit-data`

The script [main.py](./main.py) mocks an eccharts service which reads two
GRIB fields from a file, substracts them, and writes the result to a file.

You may perform that operation for un arbitrary number of times:

    $ ./run --help
    usage: main.py [-h] [--iterations N]

    options:
      -h, --help      show this help message and exit
      --iterations N  number of times to call mock service (default: 100)
    $

The script `main.py` requires:
* [earthkit-data][]
* [eccodes][]

You may also run the script relying on the version of [eccodes][] installed by
[earthkit-data][]:

     $ env ECCODES_PYTHON_USE_FINDLIBS=0 ./run

[earthkit-data]: https://earthkit-data.readthedocs.io/en/latest/
[eccodes]: https://confluence.ecmwf.int/display/ECC
