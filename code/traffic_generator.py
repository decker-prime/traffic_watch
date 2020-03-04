import argparse
import asyncio
import random
import time

import aiohttp

"""
    This program sends a number of requests to the local webserver for testing
    the traffic profiler
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


async def do_requests(ip, port, num_requests, quiet):
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
            if not quiet:
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
    parser.add_argument('--quiet', '-q', action='store_true', help="turn off output")

    args = parser.parse_args()
    port = args.port
    ip = args.ip
    quiet = args.quiet

    loop = asyncio.get_event_loop()
    # This test profile assumes the threshold_period has been set to one minute
    # For a full minute send packets at the default request rate limit,
    # (20 per sec).
    for i in range(60):
        loop.run_until_complete(do_requests(ip, port, 20, quiet))
        time.sleep(1)
    # then increase the rate to 100 per second for 20 seconds
    for i in range(20):
        loop.run_until_complete(do_requests(ip, port, 100, quiet))
        time.sleep(1)
    # then reduce the rate back to 20. The high traffic warning should disappear
    for i in range(60):
        loop.run_until_complete(do_requests(ip, port, 20, quiet))
        time.sleep(1)
