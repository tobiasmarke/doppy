import os
import pathlib
import re
import tempfile
from collections import defaultdict

import pytest
from doppy import exceptions, options, product
from doppy.data.api import Api

CACHE = "GITHUB_ACTIONS" not in os.environ


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,reason",
    [
        ("bucharest", "2021-02-18", ""),
        ("bucharest", "2021-02-17", ""),
        ("bucharest", "2021-02-16", ""),
        ("chilbolton", "2023-11-01", ""),
        ("eriswil", "2023-11-30", ""),
        ("granada", "2023-07-17", ""),
        ("hyytiala", "2023-09-20", ""),
        ("juelich", "2023-11-01", ""),
        ("kenttarova", "2023-11-01", ""),
        ("leipzig", "2023-10-12", ""),
        ("lindenberg", "2024-02-08", ""),
        ("mindelo", "2023-11-01", ""),
        ("mindelo", "2023-11-02", ""),
        ("mindelo", "2023-11-03", ""),
        ("potenza", "2023-10-28", ""),
        ("punta-arenas", "2021-11-29", ""),
        ("soverato", "2021-09-06", ""),
        ("vehmasmaki", "2022-12-30", ""),
        ("warsaw", "2023-11-01", ""),
        ("hyytiala", "2024-01-29", "some files have problems => skip them"),
        ("neumayer", "2024-02-01", "elevation angle 89"),
        ("potenza", "2024-02-05", "k-means error"),
        ("neumayer", "2024-01-30", "cannot merge header: Gate length (pts) changes"),
        ("mindelo", "2024-04-17", "nans in data"),
    ],
)
def test_stare(site, date, reason):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records_hpl = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl") and "cross" not in set(rec["tags"])
    ]
    records_bg = [rec for rec in records if rec["filename"].startswith("Background")]
    _stare = product.Stare.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl],
        data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
        bg_correction_method=options.BgCorrectionMethod.FIT,
    )


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,reason",
    [
        ("cabauw", "2023-08-26", ""),
        ("cabauw", "2021-07-29", "first"),
        ("cabauw", "2021-11-09", ""),
        ("cabauw", "2022-02-12", ""),
        ("cabauw", "2022-03-04", ""),
        ("cabauw", "2022-04-12", ""),
        ("cabauw", "2022-10-13", ""),
        ("cabauw", "2024-09-10", "last"),
        ("payerne", "2024-09-23", "Some weird stripes"),
        ("payerne", "2021-07-01", "first"),
        ("payerne", "2021-07-29", "radial distance shape changes"),
        ("payerne", "2022-02-03", ""),
        ("payerne", "2022-05-25", ""),
        ("payerne", "2022-09-30", ""),
        ("payerne", "2023-12-07", ""),
        ("payerne", "2024-11-27", "last"),
    ],
)
def test_stare_windcube(site, date, reason):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    r = re.compile(r".*fixed.*", re.IGNORECASE)
    records_fixed = [rec for rec in records if r.match(rec["filename"])]

    groups = defaultdict(list)
    group_pattern = re.compile(r".+_fixed_(.+)\.nc(?:\..+)?")
    for r in records_fixed:
        if match := group_pattern.match(r["filename"]):
            group = match.group(1)
            groups[group].append(r)

    for group, records_group in groups.items():
        _stare = product.Stare.from_windcube_data(
            data=[api.get_record_content(r) for r in records_group],
        )


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,err,reason",
    [
        ("warsaw", "2024-02-03", exceptions.NoDataError, "Missing bg files"),
        (
            "chilbolton",
            "2016-12-14",
            exceptions.NoDataError,
            "No matching data and bg files",
        ),
    ],
)
def test_bad_stare(site, date, err, reason):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records_hpl = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl") and "cross" not in set(rec["tags"])
    ]
    records_bg = [rec for rec in records if rec["filename"].startswith("Background")]

    with pytest.raises(err):
        _stare = product.Stare.from_halo_data(
            data=[api.get_record_content(r) for r in records_hpl],
            data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
            bg_correction_method=options.BgCorrectionMethod.FIT,
        )


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,system_id",
    [
        ("chilbolton", "2024-05-06", "118"),
    ],
)
def test_system_id(site, date, system_id):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records_hpl = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl") and "cross" not in set(rec["tags"])
    ]
    records_bg = [rec for rec in records if rec["filename"].startswith("Background")]
    stare = product.Stare.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl],
        data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
        bg_correction_method=options.BgCorrectionMethod.FIT,
    )
    assert stare.system_id == system_id


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,reason",
    [
        ("warsaw", "2023-11-01", ""),
    ],
)
def test_netcdf_writing(site, date, reason):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records_hpl = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl") and "cross" not in set(rec["tags"])
    ]
    records_bg = [rec for rec in records if rec["filename"].startswith("Background")]
    stare = product.Stare.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl],
        data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
        bg_correction_method=options.BgCorrectionMethod.FIT,
    )

    with tempfile.NamedTemporaryFile(suffix=".nc", delete=True) as filename:
        stare.write_to_netcdf(filename.name)

    with tempfile.NamedTemporaryFile(suffix=".nc", delete=True) as filename:
        stare.write_to_netcdf(pathlib.Path(filename.name))
