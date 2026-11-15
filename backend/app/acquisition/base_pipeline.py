"""Shared acquisition result contract and receiver validation."""
from pathlib import Path
from app.storage.files import checksum

def validate_received_files(paths: list[str], required_suffix: str = ".h5") -> list[dict]:
    if not paths:
        raise ValueError("Provider retrieval returned no files")
    validated = []; checksums=set()
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_file() or path.stat().st_size < 1024:
            raise ValueError(f"Downloaded file is missing or unexpectedly small: {path.name}")
        if required_suffix and not path.name.lower().endswith((required_suffix, ".hdf5")):
            raise ValueError(f"Unsupported downloaded file format: {path.name}")
        with path.open("rb") as source:
            signature = source.read(8)
        if signature != b"\x89HDF\r\n\x1a\n":
            raise ValueError(f"File is not a valid HDF5 granule: {path.name}")
        digest=checksum(path)
        if digest in checksums: continue
        checksums.add(digest)
        validated.append({"path": str(path), "size_bytes": path.stat().st_size, "sha256": digest})
    return validated
