# Traffic Watch

### An HTTP traffic monitor

Traffic Watch is a straightforward console application that monitors the amount of HTTP traffic to a port on your machine.

This program has been tested and verified to work on Linux (Ubuntu), handling ~1000 http requests per second.
 
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

6. Install the dependencies with 

`pip install -r requirements.txt`

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

## Improvements

### Compatibility Notes
Due to a lack of access to a MacOS machine, I learned one day before turn-in that MacOS handles sockets significantly differently from the existing unix socket design herein:
>"FreeBSD takes another approach. It *never* passes TCP or UDP packets to raw sockets. Such packets need to be read directly at the datalink layer by using libraries like libpcap or the bpf API. It also *never* passes any fragmented datagram. Each datagram has to be completeley reassembled before it is passed to a raw socket" - https://sock-raw.org/papers/sock_raw

Extending compatibility to handle both systems can be done if it's a critical requirement, but it would delay delivery by at least a couple days, and I'd need a test environment. 

### Features
I'd really like to break out the various scheduled jobs, (such as checking every x seconds for some condition and doing output, and every y seconds for some other condition), into a handy plugin arrangement. That way a new job could be easily added to the existing system.

In addition, I'd like to separate the display system, (the TUI), from the model code in traffic_watch.py, and pass a "viewmodel" object to each of the callbacks which generates display data. Then when a value is updated, they will write their values to the object, and a view class gets called to update itself. 

Also, the scheduler would be set to spin off each job in a ThreadPool, and so the only thing the main thread would be doing is updating the display, and there would be as little drag as possible on the jobs doing the calculation, and as little drag as possible on the process sniffing the packets.

It would be interesting to add the ability to listen for different kinds of traffic, in addition to HTTP Requests.

In hindsight, one of the things that ended up taking an asymmetric amount of time compared to the other components was dealing with the scapy library. All in all, it was supposed to make things easier, but between researching it, getting it to run in the test environment, later discovering its profound performance limitations when it comes to HTTP sniffing and then trying to debug that, it consumed probably 14-16 hrs of the entire 46 hrs of dev time. And I ended up writing my own socket sniffer module anyway. The performance on my test box went from ~20 requests/sec to >1,000 requests/sec with the change to my bare socket code. In the end, I added a command line switch to choose which backend to use: either my socket-based one (default) or the scapy one. So if there were ever a feature in scapy someone wanted to use, it's still there.

### Overall
I took this on in Python since I thought it would be a nice change from a few years back when I worked on network stuff in C. I thought doing it in Python would take a significantly shorter period of time. Well, it is significantly fewer *lines* than a C program doing the same thing, but I think overall implementation time was similar, and I don't remember having to struggle for performance so much with the compiled language. 

On the other hand, I've been using Python for a few years, and this project certainly took me to new corners of the language libraries. 

The program is written to try for maximum clarity for people who may not know the language inside and out. I wrote, for example, a list comprehension that had an early loop breakout, and replaced it with an ordinary set of for statements because it would more clearly convey to maintainers the code's intention.

Thanks for your time, and I appreciate your consideration.
