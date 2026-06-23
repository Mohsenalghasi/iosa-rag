import httpx
from pathlib import Path
from iosa.logger import setup_logger

log=setup_logger("iosa.ingestion.downloader")

def read_sources(path: Path) -> list[str]:
    """Read URLs from a text file, skipping comments and blanks."""
    urls = []
    with open(path, "r") as f:
        for line in f:
            line=line.strip()
            if line and not line.startswith("#"):
                urls.append(line)

    log.info(f"Loaded {len(urls)} URLs from {path}")
    return urls


def download_pdf(url: str, output_dir: Path) -> bool:
    """Download a single PDF from a URL into output_dir. Returns True on success."""
    filename = url.split("/")[-1]
    output_path = output_dir / filename

    if output_path.exists():
        log.info(f"Already downloaded, skipping: {filename}")
        return True

    log.info(f"Downloading: {url}")

    try:
        response = httpx.get(url, timeout=30, follow_redirects=True)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        log.info(f"Saved: {output_path}")
        return True

    except httpx.HTTPError as e:
        log.error(f"Failed to download {url}: {e}")
        return False

if __name__ == "__main__":
    sources_file = Path("config/sources.txt")
    output_dir = Path("data/raw")

    urls = read_sources(sources_file)
    log.info(f"Starting download of {len(urls)} files")

    success_count = 0
    for url in urls:
        if download_pdf(url, output_dir):
            success_count += 1

    log.info(f"Done. {success_count}/{len(urls)} files downloaded successfully")