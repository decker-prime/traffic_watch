
# Traffic Watch

### An HTTP traffic monitor

Traffic Watch is a straightforward console application that monitors the amount of HTTP traffic to a port on a machine.

This program has been tested and verified to work on Linux (Ubuntu and Mint test platforms tested, presumably it will run on other flavors as well). 
 
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
There are two different tests included, one functional test and a unit test suite.

### Unit Test
The unit test suite to exercise the alerting logic is in [test_traffic_alert.py](https://github.com/decker-prime/traffic_watch/blob/master/code/test_traffic_alert.py "test_traffic_alert.py").  This runs with the python 'unittest' framework, which can be executed with:

`$ python -m unittest test_traffic_alert.py`

### Functional Test
The functional test is in [functional_test_runner.sh](https://github.com/decker-prime/traffic_watch/blob/master/code/functional_test_runner.sh). This test starts a dummy webserver and traffic generator, then loads the traffic watch application for monitoring. 

To run this test, make sure the python environment is still activated, and flask isn't already running. Then run this test via:

`$ bash -i functional_test_runner.sh`

>Note: To keep test times reasonable, the alert time threshold is set to one minute instead of two. 

This test will send requests at a rate of 20 requests/sec for one minute. Then that rate is increased to 100 requests/sec for 20 seconds. This will cause an alert. After the 20 seconds have passed, the request rate will again drop to 20 req/sec for 30 seconds. The high traffic alert will remain engaged for (roughly) 1 minute and 22 seconds, and then recover.

Subsequently pressing Ctrl-C ends the test, and should kill the flask server that was started at the beginning of the script.

## Improvements

### Compatibility 
At the present time, the socket capture code code works well for linux. Given the opportunity, I'd like to expand it using the pcap libraries to work on MacOS. I don't presently have access to a MacOS machine, so it would take some doing.
 
As you're aware, MacOS handles raw sockets significantly differently from the existing unix/linux design:
>"[FreeBSD] *never* passes TCP or UDP packets to raw sockets. Such packets need to be read directly at the datalink layer by using libraries like libpcap or the bpf API. It also *never* passes any fragmented datagram. Each datagram has to be completeley reassembled before it is passed to a raw socket" - https://sock-raw.org/papers/sock_raw

OS availability issue aside, it would be straightforward to add that functionality.

### Features
For design features and changes, I'd really like to break out the various scheduled jobs, (such as checking every x seconds for some condition and doing output, and every y seconds for some other condition), into a plugin arrangement. That way a new job could be easily added to the existing system. Further refinement of the view (as in model/view/controller) code would also be beneficial. 

As far as runtime features go, I'd love to expand it to do more sophisticated trending analysis... to see if certain parts of the website are more popular than others at given times of the day by matching the source IPs with a geographic search, etc.

It would be interesting to add the ability to listen for different kinds of traffic, in addition to HTTP Requests.

### Challenges

One of the things that ended up taking a ridiculously asymmetric amount of time compared to the other components was dealing with the scapy library. It is allegedly supposed to make things easier, but between researching it, getting it to run in the test environment, later discovering its profound performance limitations when it comes to HTTP sniffing, and then trying to debug that thinking it was my fault, consumed probably 12-14 hrs of the entire 46 hrs of dev time.

 And I ended up writing my own socket sniffer module anyway. The performance on my test box went from ~20 requests/sec to >1,000 requests/sec with the change to my simple raw socket code. In the end, I added a command line switch to choose which backend to use: either my socket-based one (default) or the scapy one. So if there were ever a feature in scapy someone wanted to use, it's still there.

### Overall
Some years ago I worked on a proxy project that was written in C, and so I chose to do this project in Python because I thought it would take significantly less time, and I figured I'd learn something. Well, it did turn out to be significantly fewer *lines* than a C program doing the same thing. But the overall implementation time was not profoundly shorter. Python enables some issues to become a breeze - running code in other threads or subprocesses, multiprocess communication, maintenance ease, etc. but when dependent upon performance, it still seems many times slower than compiled C.

On the other hand, I've been using Python for three years, and this project took me to new corners of the language libraries, which was interesting.

This program works right out of the box on my test machines, so if there are issues running it, please reach out. 
