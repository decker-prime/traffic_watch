
# Traffic Watch

### An HTTP traffic monitor

Traffic watch is a straightforward console application that monitors the amount of HTTP traffic to a port on your machine.

This program has been tested and verified to work on Linux, handling ~1000 http requests per second.
 
## Installation
1. Traffic watch requires Python 3.7
Due to the variety of different platforms and their various package installation methods, please see the Python [download page](https://www.python.org/downloads/) if you need instructions on its installation. 

2. Build a virtual environment - Using virtualenv we'll create a isolated working environment, so the libraries we install here will not affect any existing python setup on the machine. Once you have python3 installed, install virtualenv using:
`$ sudo pip install virtualenv `

3. Then create a virtual environment. We'll end up cloning the app into one of the subfolders. Something like:
`mkdir ~/py37env`
`virtualenv ~/py37env`

4. To activate the new environment, cd to the environment's bin folder and activate it:
`cd ~/py37env/bin`
`source activate py37env`
Now anything we pip install will be in this environment, and isolated from the rest of the box's python setup.
5. clone or download this project, and extract it in a memorable location, such as `~/py37env/traffic_watch`. `cd` to its main folder, (the one with this README.md in it)
6. Install the dependencies with `pip install -r requirements.txt`
7. The code exists in the `traffic_watch/code` subfolder, so `cd` there to run. This is 100% python, so no compilation step is necessary. 

## Running

>Note: This program requires root access or a sudo to run

The primary executable is [traffic_watch.py](https://github.com/decker-prime/traffic_watch/blob/master/code/traffic_watch.py "traffic_watch.py")

I've found that in linux, since sudo usually doesn't honor virtualenv's python3 path, that the following will work, to for example, monitor port 5000:

``$ sudo `which python` traffic_watch.py --port 5000``

You may want to limit the http results to the ip address of the webserver. This will filter out any incoming packet that has a different destination ip. If the ip address were 10.12.3.201 would be:

``$ sudo `which python` traffic_watch.py --port 5000 -ip 10.12.3.201``

Or, if testing from the same box, you may want to use the loopback address:

``$ sudo `which python` traffic_watch.py --port 5000 -ip 127.0.0.1``

#### Dummy Web Server and Traffic Generator

There is a simple flask webserver, [simple_webserver.py](https://github.com/decker-prime/traffic_watch/blob/master/code/simple_webserver.py "simple_webserver.py"), to aid in the testing of the traffic watch program.

The flask server has some output, so it's best to start it in another terminal window. Activate the python environment, navigate to the `traffic_watch/code` directory and type:

``$ python simple_webserver.py``

This will start a simple server listening on all ip's, port 5000

#### Traffic Generator
There is very simple traffic generator, [traffic_generator.py](https://github.com/decker-prime/traffic_watch/blob/master/code/traffic_generator.py "traffic_generator.py"), that simply sends 1000 HTTP Requests to 127.0.0.1:5000, with various 'section' names in the URLs. This may be run repeatedly while traffic_watch.py is running to provide something for the traffic_watch.py instance to do. It can be run using:

`$ python traffic_generator.py`

## Tests 
As requested, there is a unit test suite to exercise the alerting logic in [test_traffic_alert.py](https://github.com/decker-prime/traffic_watch/blob/master/code/test_traffic_alert.py "test_traffic_alert.py").  This runs with the python unittest framework, which can be executed with:

`$ python -m unittest test_traffic_alert.py`

## Compatibility Notes
Due to my lack of access to a MacOS machine, I learned one day before turn-in that MacOS handles sockets significantly differently from the existing unix socket design herein:
>"FreeBSD takes another approach. It *never* passes TCP or UDP packets to raw sockets. Such packets need to be read directly at the datalink layer by using libraries like libpcap or the bpf API. It also *never* passes any fragmented datagram. Each datagram has to be completeley reassembled before it is passed to a raw socket" - https://sock-raw.org/papers/sock_raw

Extending compatibility to handle both systems can be done if it's a critical requirement, but it would delay delivery by at least a couple days, (since I have other obligations). 
