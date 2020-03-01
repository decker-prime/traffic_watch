import asyncio
import random

import aiohttp

"""
    This program sends a number of requests to the local webserver for testing
    a packet sniffer.
"""

sections = ['foo', 'bar', 'baz', 'spiffy', 'zoom']


async def fetch(session, url):
    """
    A coroutine that simply calls 'get' against a url, and returns the response
    @param session: The session, previously set up by aiohttp.ClientSession()
    @param url: The destination url
    @return: A string of response text
    """
    async with session.get(url) as response:
        return await response.text()


async def do_requests(num_requests):
    """
    Take the number of requests and spin them off to the fetching coroutine
    @param num_requests: the number of requests to send
    @return: None
    """
    async with aiohttp.ClientSession() as session:
        for i in range(num_requests):
            html = await fetch(session,
                               f'http://127.0.0.1:5000/{random.choice(sections)}/index.html{i}')
            # await asyncio.sleep(0.0001)
            print(html)


if __name__ == '__main__':
    """
    The driver for the request sender
    """
    loop = asyncio.get_event_loop()
    for i in range (100):
            loop.run_until_complete(do_requests(100))
            #asyncio.sleep(1)

