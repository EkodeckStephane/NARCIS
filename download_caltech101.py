from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import time
import urllib.error
import urllib.parse
import urllib.request


API = "https://datasets-server.huggingface.co/rows"
DATASET = "mteb/Caltech101"


def fetch_json(url: str, attempts: int = 10) -> dict:
    for attempt in range(attempts):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "NARCIS/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            retryable = error.code == 429 or 500 <= error.code < 600
            if not retryable or attempt == attempts - 1:
                raise
            retry_after = int(error.headers.get("Retry-After", "5"))
            time.sleep(min(60, max(retry_after, 2 ** attempt)))
    raise RuntimeError("Unreachable retry state")


def page(
    split: str,
    offset: int,
    cache: Path,
    length: int = 100,
) -> dict:
    cached = cache / f"{split}_{offset:05d}.json"
    if cached.exists():
        return json.loads(cached.read_text(encoding="utf-8"))
    query = urllib.parse.urlencode(
        {
            "dataset": DATASET,
            "config": "default",
            "split": split,
            "offset": offset,
            "length": length,
        }
    )
    result = fetch_json(f"{API}?{query}")
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps(result), encoding="utf-8")
    return result


def download_one(item: tuple[str, Path], attempts: int = 8) -> None:
    url, destination = item
    if destination.exists() and destination.stat().st_size > 0:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    for attempt in range(attempts):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "NARCIS/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                temporary.write_bytes(response.read())
            temporary.replace(destination)
            return
        except (OSError, TimeoutError, urllib.error.URLError):
            temporary.unlink(missing_ok=True)
            if attempt == attempts - 1:
                raise
            time.sleep(min(30, 2 ** attempt))


def collect_split(split: str, root: Path) -> list[tuple[str, Path]]:
    cache = root / "metadata"
    first = page(split, 0, cache)
    labels = first["features"][1]["type"]["names"]
    total = first["num_rows_total"]
    rows = first["rows"]
    for offset in range(len(rows), total, 100):
        time.sleep(0.25)
        rows.extend(page(split, offset, cache)["rows"])

    downloads = []
    for entry in rows:
        row = entry["row"]
        label = labels[row["label"]]
        source = row["image"]["src"]
        suffix = Path(urllib.parse.urlparse(source).path).suffix or ".jpg"
        destination = (
            root
            / "images"
            / label
            / f"{split}_{entry['row_idx']:05d}{suffix.lower()}"
        )
        downloads.append((source, destination))
    return downloads


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dataset_external/caltech101"),
    )
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    downloads = collect_split("train", args.output)
    downloads.extend(collect_split("test", args.output))
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(download_one, downloads))

    manifest = {
        "dataset": "Caltech-101",
        "source": "CaltechDATA record mzrjq-6wc02",
        "distribution_mirror": DATASET,
        "images": len(downloads),
        "splits": ["train", "test"],
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
