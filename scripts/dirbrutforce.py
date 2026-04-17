try:
    import asyncio
    import aiofiles
    import aiohttp
except ImportError:
    print('[modules]\033[91m following modules are required!\033[0m => [ aiofiles , asyncio , aiohttp ]')
    print('[hint]\033[91m to install them run the following\033[0m => \033[93mpip install aiofiles aiohttp asyncio\033[0m')
    exit(1)

import argparse
from typing import Dict, List

# =========================
# Globals / Config
# =========================
VALID_STATUS_CODES = {200, 204, 301, 302, 307, 403}
discovered_paths: Dict[str, int] = {}


# =========================
# File Handling
# =========================
async def load_wordlist(file_path: str) -> List[str]:
    try:
        async with aiofiles.open(file_path, mode="r") as f:
            content = await f.read()
            return [line.strip() for line in content.splitlines() if line.strip()]
    except FileNotFoundError:
        print(f"[!] Wordlist not found: {file_path}")
        exit(1)


# =========================
# HTTP Logic
# =========================
async def fetch_path(
    base_url: str,
    path: str,
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    timeout: float,
) -> None:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"

    async with semaphore:
        try:
            async with session.get(url, timeout=timeout) as response:
                if response.status in VALID_STATUS_CODES:
                    discovered_paths[url] = response.status
                    print(f"[+] {response.status} -> {url}")
        except asyncio.TimeoutError:
            pass
        except aiohttp.ClientError:
            pass


# =========================
# CLI Arguments
# =========================
def parse_args():
    parser = argparse.ArgumentParser(
        description="Async Directory Bruteforcer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("url", help="Target base URL")
    parser.add_argument("-w", "--wordlist", required=True, help="Path to wordlist")
    parser.add_argument("-t", "--timeout", type=float, default=1.0, help="Request timeout")
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=100,
        help="Max concurrent requests",
    )

    return parser.parse_args()


# =========================
# UI Helpers
# =========================
def print_banner():
    print("#" * 50)
    print("# Directory Bruteforcer ")
    print("#" * 50)


def print_summary():
    GREEN = '\033[92m'
    RESET_COLOR = '\033[0m'

    print("\n" + "=" * 50)
    print(f"Finished. Found {len(discovered_paths)} valid paths.\n")

    for url, status in discovered_paths.items():
        if status == 200:
            print(f"[{GREEN}{status}{RESET_COLOR}] {url}")
        else:
            print(f"[{YELLOW}{status}{RESET_COLOR}] {url}")


# =========================
# Main Logic
# =========================
async def main():
    args = parse_args()
    print_banner()

    words = await load_wordlist(args.wordlist)
    print(f"[i] Loaded {len(words)} words")

    semaphore = asyncio.Semaphore(args.concurrency)

    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_path(args.url, word, session, semaphore, args.timeout)
            for word in words
        ]

        print("[i] Starting scan...\n")
        await asyncio.gather(*tasks)

    print_summary()


# =========================
# Entry Point
# =========================
if __name__ == "__main__":
    asyncio.run(main())