from pathlib import Path
import zipfile, shutil

BASE = Path(__file__).resolve().parents[1]
raw_dir = BASE / "data" / "raw"
processed_dir = BASE / "data" / "processed"
processed_dir.mkdir(parents=True, exist_ok=True)

outer_zip = next(raw_dir.glob("*.zip"))
outer_extract = processed_dir / "outer_extract"
dataset_extract = processed_dir / "dataset_extract"

if outer_extract.exists():
    shutil.rmtree(outer_extract)
if dataset_extract.exists():
    shutil.rmtree(dataset_extract)

outer_extract.mkdir(parents=True, exist_ok=True)
dataset_extract.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(outer_zip, "r") as zf:
    zf.extractall(outer_extract)

nested_zip = next(outer_extract.rglob("data.zip"))

with zipfile.ZipFile(nested_zip, "r") as zf:
    zf.extractall(dataset_extract)

print("Dataset extracted to:", dataset_extract)

