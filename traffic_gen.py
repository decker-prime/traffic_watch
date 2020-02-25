import aiohttp
import asyncio

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def do_requests():
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, 'http://127.0.0.1:5000/index.html')
        print(html)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(do_requests())
