"""GPM IMERG monthly acquisition with persistent NASA granule reuse."""
from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from typing import Any

from app.acquisition.base_pipeline import validate_received_files
from app.connectors.earthdata import EarthdataGPMConnector, granule_metadata
from app.models.schemas import AcquisitionResult
from app.storage import jobs
from app.storage.files import investigation_dir


def _granule_identity(granule: Any) -> tuple[str, str]:
    umm = granule.get("umm", {})
    meta = granule.get("meta", {})
    granule_id = umm.get("GranuleUR") or meta.get("concept-id")
    if not granule_id:
        raise ValueError("NASA CMR granule is missing its stable identifier")
    raw_name = Path(str(umm.get("GranuleUR") or granule_id).rsplit(":", 1)[-1]).name
    if not raw_name.lower().endswith((".h5", ".hdf5")):
        raw_name += ".h5"
    return str(granule_id), raw_name


def _is_valid_cached(path: Path, expected_checksum: str) -> bool:
    try:
        if not path.is_file() or path.stat().st_size < 1024:
            return False
        with path.open("rb") as stream:
            if stream.read(8) != b"\x89HDF\r\n\x1a\n":
                return False
        return jobs_checksum(path) == expected_checksum
    except OSError:
        return False


def jobs_checksum(path: Path) -> str:
    from app.storage.files import checksum
    return checksum(path)


def _materialize(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def _cache_validated_file(key: str, source: Path, cache_root: Path, validation: dict, *, move_source: bool = False) -> Path:
    cache_path = cache_root / f"{hashlib.sha256(key.encode('utf-8')).hexdigest()}{source.suffix.lower()}"
    temporary = cache_path.with_suffix(cache_path.suffix + ".tmp")
    if move_source:
        try:
            os.replace(source, temporary)
        except OSError:
            shutil.copy2(source, temporary)
    else:
        shutil.copy2(source, temporary)
    os.replace(temporary, cache_path)
    jobs.cache_granule(key, str(cache_path.resolve()), validation["sha256"], validation["size_bytes"])
    return cache_path


async def acquire(request, investigation_id: str) -> tuple[AcquisitionResult, list[dict]]:
    connector = EarthdataGPMConnector()
    granules = await connector.discover(request.time_range.model_dump(mode="json"), request.geometry)
    if not granules:
        raise RuntimeError("NASA CMR returned no GPM IMERG Monthly V07 granules for this request")

    folder = investigation_dir(investigation_id)
    cache_root = (jobs.DATA_ROOT / "raw" / "earthdata" / "cache").resolve()
    cache_root.mkdir(parents=True, exist_ok=True)
    entries: list[tuple[str, str, Any]] = []
    seen: set[str] = set()
    for granule in granules:
        key, filename = _granule_identity(granule)
        if key not in seen:
            entries.append((key, filename, granule))
            seen.add(key)

    pending = []
    paths_by_key: dict[str, Path] = {}
    cache_hits = 0
    for key, filename, granule in entries:
        cached = jobs.get_cached_granule(key)
        if cached:
            cached_path = Path(cached["file_path"]).resolve()
            try:
                cached_path.relative_to(cache_root)
            except ValueError:
                cached_path = Path()
            if cached_path != Path() and _is_valid_cached(cached_path, cached["checksum"]):
                target = folder / filename
                _materialize(cached_path, target)
                paths_by_key[key] = target.resolve()
                cache_hits += 1
                continue
        # Reuse files left by an interrupted/failed earlier attempt for the same investigation.
        existing = folder / filename
        if existing.is_file():
            validation = validate_received_files([str(existing)])[0]
            _cache_validated_file(key, existing, cache_root, validation)
            paths_by_key[key] = existing.resolve()
            cache_hits += 1
            continue
        pending.append((key, filename, granule))

    downloaded_paths = await connector.retrieve([entry[2] for entry in pending], folder) if pending else []
    validated_downloads = validate_received_files(downloaded_paths) if downloaded_paths else []
    by_name: dict[str, Path] = {Path(item["path"]).name.lower(): Path(item["path"]) for item in validated_downloads}
    for key, filename, _granule in pending:
        downloaded = by_name.get(filename.lower())
        if downloaded is None:
            # Earthaccess can normalize the original identifier casing; require an unambiguous match.
            matches = [p for name, p in by_name.items() if Path(name).stem.lower() == Path(filename).stem.lower()]
            if len(matches) != 1:
                raise ValueError(f"Could not match downloaded NASA granule to {filename}")
            downloaded = matches[0]
        # Receiver validation already checked size, HDF5 signature, and SHA256.
        verified = next(item for item in validated_downloads if Path(item["path"]) == downloaded)
        cache_path = _cache_validated_file(key, downloaded, cache_root, verified, move_source=True)
        target = folder / filename
        _materialize(cache_path, target)
        paths_by_key[key] = target.resolve()

    paths = list(dict.fromkeys(str(paths_by_key[key]) for key, _name, _g in entries))
    validations = validate_received_files(paths)
    result = AcquisitionResult(
        investigation_id=investigation_id, provider="earthdata", dataset_id="gpm_imerg_monthly", product_version="07",
        status="completed", raw_files=[item["path"] for item in validations], raw_format="HDF5", requested_variable=request.variable,
        requested_time_range=request.time_range, requested_geometry=request.geometry,
        source_metadata={"catalog": "NASA CMR", "short_name": connector.short_name, "version": connector.version,
                         "granules": [granule_metadata(g) for g in granules]},
        acquisition_metadata={"granule_count": len(entries), "unique_validated_file_count": len(validations),
                              "duplicate_files_removed": len(granules)-len(entries), "cache_hits": cache_hits,
                              "downloaded_granule_count": len(pending), "validated_files": validations})
    return result, validations
