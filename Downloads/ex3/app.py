import time
import aiohttp
import asyncio
import concurrent.futures
import os
from threading import Event

url = 'http://34.69.146.51:5000/level2'
max_batch_limit = 1_000_000
batch_size = 5000
max_workers = os.cpu_count() * 4 or 1

async def fetch_batch(session, start, end):
    params = {'start': start, 'end': end}
    async with session.get(url, params=params) as response:
        if response.status == 200:
            return await response.json()
        elif response.status == 400:
            print(f"No more data to fetch in range {start} to {end}. Stopping search.")
            return None
        else:
            print(f"Failed to retrieve data: {response.status}")
            return None

async def search_range(start, step, stop_event):
    async with aiohttp.ClientSession() as session:
        while start <= max_batch_limit and not stop_event.is_set():
            end = start + batch_size
            print(f"Fetching data from {start} to {end}...")
            
            data = await fetch_batch(session, start, end)
            if not data:
                break

            for item in data:
                if 'flag' in item:
                    print(f"Flag found: {item['flag']}")
                    stop_event.set()
                    return True

            start += step * max_workers

    return False

def thread_worker(worker_id, step, stop_event):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(search_range(worker_id * step, step, stop_event))

def main():
    stop_event = Event()
    step = batch_size

    start_time = time.time()  # Start the timer

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(thread_worker, i, step, stop_event) for i in range(max_workers)]
        
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                print("Flag found! Stopping further search.")
                stop_event.set()
                
                end_time = time.time()  # Stop the timer
                total_time = end_time - start_time
                print(f"Total time taken: {total_time:.2f} seconds")

                break
        else:
            print("Flag not found in any batch.")

if __name__ == "__main__":
    main()
