try:
    import asyncio
    import aiofiles
    import aiohttp

except ImportError:
    print('the following modules are required => [ aiofiles , asyncio , aiohttp ]')
    print('--threading to use multithreading instead of async ')

# Global modules ( builtins )
import argparse
from typing import Dict
import requests 


# Global variables shared among all classes
FOUND_URLS: Dict[str , int] = {}


# Asyncio Logic
class Async_Brute():
    async def open_wordist(self , path_to_file:str) -> list:
        pass

    async def probe_url() -> None:
        pass

    async def brute() -> None:
        pass 
    
# Threading logic
class Threaded_Brute():
    from threading import Lock
    from concurrent.futures import ThreadPoolExecutor

    def open_wordlist(self , path_to_file:str) -> list:
        try:
                with open(path_to_file , 'r') as ptf:
                    words = (ptf.read()).split('\n')
                    return words

        except FileNotFoundError:
            print(f'{path_to_file} not found! , please check if it exists')
            exit(1)

    def probe_url(url:str , word:str) -> None:
        pass 


def main() -> None:
    pass 

if __name__ == "__main__":
    main()