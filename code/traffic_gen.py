import aiohttp
import asyncio

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def do_requests(num_requests):
    async with aiohttp.ClientSession() as session:
        for i in range(num_requests):
                html = await fetch(session,
                                   f'http://127.0.0.1:5000/index.html{i}')
                #await asyncio.sleep(0.0001)
                print(html)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(do_requests(1000))
