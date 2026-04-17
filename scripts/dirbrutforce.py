try:
    import asyncio
    import aiofiles
    import aiohttp
except ImportError:
    print('[ERR] Missing modules => aiofiles, aiohttp')
    print('[HINT] pip install aiofiles aiohttp')
    exit(1)

import argparse
from typing import Dict, List

# =========================
# Globals / Config
# =========================
VALID_STATUS_CODES = {200, 204, 301, 302, 307, 403}
discovered_paths: Dict[str, int] = {}

# Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RED = '\033[91m'
RESET = '\033[0m'


# =========================
# File Handling
# =========================
async def load_wordlist(file_path: str) -> List[str]:
    try:
        async with aiofiles.open(file_path, mode="r") as f:
            content = await f.read()
            return [line.strip() for line in content.splitlines() if line.strip()]
    except FileNotFoundError:
        print(f"{RED}[ERR]{RESET} Wordlist not found: {file_path}")
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
                    color = GREEN if response.status == 200 else YELLOW
                    print(f"{color}[{response.status}]{RESET} {url}")
        except asyncio.TimeoutError:
            pass
        except aiohttp.ClientError:
            pass


async def detect_wildcard(url: str, session: aiohttp.ClientSession) -> None:
    import string, random

    print(f"{BLUE}[INFO]{RESET} Running wildcard detection (20 checks)")

    BASELINE_SIZE = None

    for _ in range(20):
        random_text = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        full_url = f"{url.rstrip('/')}/{random_text}"

        try:
            async with session.get(full_url) as resp:
                text = await resp.text()

                if resp.status in VALID_STATUS_CODES:
                    if BASELINE_SIZE is None:
                        BASELINE_SIZE = len(text)

                    if len(text) == BASELINE_SIZE:
                        print(f"{YELLOW}[WARN]{RESET} Wildcard likely: {full_url} [{resp.status}]")
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
    parser.add_argument("-t", "--timeout", type=float, default=1.0)
    parser.add_argument("-c", "--concurrency", type=int, default=100)
    parser.add_argument('--detect-WildCard', action='store_true')

    return parser.parse_args()


# =========================
# UI Helpers
# =========================
def print_banner():
    print("=" * 50)
    print(" Async Directory Scanner ")
    print("=" * 50)


def print_summary():
    print("\n" + "=" * 50)
    print(f"Finished. Found {len(discovered_paths)} paths.\n")

    for url, status in discovered_paths.items():
        color = GREEN if status == 200 else YELLOW
        print(f"{color}[{status}]{RESET} {url}")


def confirm():
    while True:
        choice = input("[?] Continue? (y/n): ").lower().strip()
        if choice in ('y', 'n'):
            return choice == 'y'
        print("[!] Invalid input")


# =========================
# Main Logic
# =========================
async def main():
    args = parse_args()
    print_banner()

    words = await load_wordlist(args.wordlist)
    print(f"{BLUE}[INFO]{RESET} Loaded {len(words)} words")

    semaphore = asyncio.Semaphore(args.concurrency)

    async with aiohttp.ClientSession() as session:
        if args.detect_WildCard:
            await detect_wildcard(args.url, session)

        if not confirm():
            print(f"{RED}[ERR]{RESET} Scan aborted")
            exit(1)

        print("-" * 50)
        print(f"{BLUE}[INFO]{RESET} Starting scan...\n")

        tasks = [
            fetch_path(args.url, word, session, semaphore, args.timeout)
            for word in words
        ]

        await asyncio.gather(*tasks)

    print_summary()


# =========================
# Entry Point
# =========================
if __name__ == "__main__":
    asyncio.run(main())