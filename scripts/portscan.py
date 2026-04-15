import asyncio
import argparse
from typing import Dict

"""
Async Port Scanner
------------------
A simple asynchronous TCP port scanner that:
- Scans a target host over a given port range
- Attempts banner grabbing
- Optionally sends a payload if no banner is received

Last Update: 15/04/2026
Author: TAH4 (refactored)
"""

# Global storage for open ports and their banners
OPEN_PORTS: Dict[int, str] = {}


# -----------------------------
# Core Scanning Logic
# -----------------------------
async def scan_single_port(
    host: str,
    port: int,
    buffer_size: int,
    payload: str
) -> None:
    """
    Attempt to connect to a single port and grab service/banner info.

    Args:
        host (str): Target host (IP or domain)
        port (int): Port number to scan
        buffer_size (int): Max bytes to read from socket
        payload (str): Payload sent if no banner is received
    """
    try:
        reader, writer = await asyncio.open_connection(host, port)

        print(f"[+] Open port found: {port}")

        # catch the port
        OPEN_PORTS[port] = 'no banner received'

        # Try to read banner
        banner = (await reader.read(buffer_size)).decode(errors="ignore").strip()

        # If no banner, send payload
        if not banner:
            print(f"[>] Sending payload to port {port}: {payload!r}")
            writer.write(payload.encode())
            await writer.drain()

            banner = (await reader.read(buffer_size)).decode(errors="ignore").strip()

        OPEN_PORTS[port] = banner or "No banner received"

        writer.close()
        await writer.wait_closed()

    except OSError:
        # Closed port / unreachable
        pass


async def scan_with_limit(
    host: str,
    port: int,
    timeout: float,
    buffer_size: int,
    payload: str,
    semaphore: asyncio.Semaphore
) -> None:
    """
    Wrap scanning with concurrency limit and timeout.

    Args:
        host (str): Target host
        port (int): Port number
        timeout (float): Timeout per scan
        buffer_size (int): Read buffer size
        payload (str): Payload to send
        semaphore (asyncio.Semaphore): Concurrency limiter
    """
    async with semaphore:
        try:
            await asyncio.wait_for(
                scan_single_port(host, port, buffer_size, payload),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            print(f"[-] Timeout on port {port}")


# -----------------------------
# CLI Arguments
# -----------------------------
def parse_arguments():
    """
    Parse CLI arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Async TCP Port Scanner with Banner Grabbing"
    )

    parser.add_argument("host", help="Target host (IP or domain)")
    parser.add_argument(
        "-r", "--range",
        type=int,
        default=1024,
        help="Scan ports from 1 to N (default: 1024)"
    )
    parser.add_argument(
        "--payload",
        default="hello",
        help="Payload sent if no banner is received"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=float,
        default=0.5,
        help="Timeout per port (seconds)"
    )
    parser.add_argument(
        "--buffer-size",
        type=int,
        default=4096,
        help="Max bytes to read from socket"
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=500,
        help="Maximum concurrent connections"
    )

    return parser.parse_args()


# -----------------------------
# UI / Menu Display
# -----------------------------
def print_scan_summary(host: str, port_range: int):
    """
    Print scan summary in a clean menu format.
    """
    print("\n" + "=" * 50)
    print("        ASYNC PORT SCANNER RESULTS")
    print("=" * 50)
    print(f"Target       : {host}")
    print(f"Port Range   : 1 - {port_range}")
    print(f"Open Ports   : {len(OPEN_PORTS)}")
    print("=" * 50)


def print_results():
    """
    Print discovered open ports in a table-like format.
    """
    if not OPEN_PORTS:
        print("\n[!] No open ports found.")
        return

    print("\n[+] Open Ports & Services:\n")
    print(f"{'PORT':<10} | SERVICE")
    print("-" * 50)

    for port, banner in sorted(OPEN_PORTS.items()):
        print(f"{port:<10} | {banner}")


# -----------------------------
# Entry Point
# -----------------------------
async def main():
    """
    Main execution function:
    - Parse arguments
    - Launch async scan tasks
    - Display results
    """
    args = parse_arguments()

    semaphore = asyncio.Semaphore(args.max_concurrency)

    tasks = [
        scan_with_limit(
            args.host,
            port,
            args.timeout,
            args.buffer_size,
            args.payload,
            semaphore
        )
        for port in range(1, args.range + 1)
    ]

    try:
        await asyncio.gather(*tasks)

        print_scan_summary(args.host, args.range)
        print_results()

    except KeyboardInterrupt:
        print("\n[!] Scan interrupted by user.")
    except Exception as e:
        print(f"[!] Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())