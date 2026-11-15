import asyncio

import h5py
import numpy as np
from shapely.geometry import box, mapping

from app.acquisition import earthdata_pipeline
from app.models.schemas import InvestigationRequest
from app.storage import jobs


def test_repeated_investigation_reuses_validated_granule(monkeypatch, tmp_path):
    monkeypatch.setattr(jobs, "DB_PATH", tmp_path / "jobs.sqlite3")
    monkeypatch.setattr(jobs, "DATA_ROOT", tmp_path / "data")
    jobs.initialize()
    granule = {"meta": {"concept-id": "GPM_001"},
               "umm": {"GranuleUR": "GPM_3IMERGM_200006.V07B.HDF5", "TemporalExtent": {}}}
    counts = {"retrieve": 0}

    async def discover(self, _time_range, _geometry):
        return [granule]

    async def retrieve(self, granules, directory):
        counts["retrieve"] += 1
        paths = []
        for item in granules:
            path = directory / item["umm"]["GranuleUR"]
            with h5py.File(path, "w") as h5:
                h5.create_dataset("payload", data=np.arange(1024, dtype="i4"))
            paths.append(str(path.resolve()))
        return paths

    monkeypatch.setattr(earthdata_pipeline.EarthdataGPMConnector, "discover", discover)
    monkeypatch.setattr(earthdata_pipeline.EarthdataGPMConnector, "retrieve", retrieve)
    request = InvestigationRequest(variable="precipitation", geometry=mapping(box(75, 8, 77, 10)),
                                   time_range={"start": "2000-06-01", "end": "2000-06-30"})

    first, first_files = asyncio.run(earthdata_pipeline.acquire(request, "investigation-one"))
    second, second_files = asyncio.run(earthdata_pipeline.acquire(request, "investigation-two"))

    assert counts["retrieve"] == 1
    assert first.acquisition_metadata["cache_hits"] == 0
    assert second.acquisition_metadata["cache_hits"] == 1
    assert len(first_files) == len(second_files) == 1
    assert first_files[0]["sha256"] == second_files[0]["sha256"]
    assert first_files[0]["path"] != second_files[0]["path"]
    assert jobs.get_cached_granule("GPM_3IMERGM_200006.V07B.HDF5") is not None


def test_cmr_granule_filename_drops_product_prefix():
    key, filename = earthdata_pipeline._granule_identity({
        "meta": {"concept-id": "GPM_001"},
        "umm": {"GranuleUR": "GPM_3IMERGM.07:3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5"},
    })
    assert key.startswith("GPM_3IMERGM.07:")
    assert filename == "3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5"
