import argparse
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


async def do_requests(ip, port, num_requests):
    """
    Take the number of requests and spin them off to the fetching coroutine
    @param ip: The destination ip
    @param port: The destination port
    @param num_requests: the number of requests to send
    @return: None
    """
    async with aiohttp.ClientSession() as session:
        for i in range(num_requests):
            html = await fetch(session,
                               f'http://{ip}:{port}/{random.choice(sections)}/index.html{i}')
            print(html)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='This program sends a number of requests to a predefined' +
                    'server')
    parser.add_argument('--port', '-p', type=int, help="The port to monitor",
                        default=5000)
    parser.add_argument('-ip', type=str,
                        help="(Default: 127.0.0.1) - the ip address to use" + \
                             "for the requests.",
                        default="127.0.0.1")

    args = parser.parse_args()
    port = args.port
    ip = args.ip

    loop = asyncio.get_event_loop()
    for i in range(10):
        loop.run_until_complete(ip, port, do_requests(100))
        asyncio.sleep(1)
