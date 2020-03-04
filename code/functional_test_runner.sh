#!/bin/bash
# For this test to work, please run using:
# $ bash -i functional_test_runner.sh

# start the flask webserver
FLASK_APP=simple_webserver.py flask run &> /dev/null &
echo sleeping 3s to allow webserver to finish setting up
sleep 3s

# start the traffic generator
python traffic_generator.py --quiet &> /dev/null &

# start the traffic watch utility.
# instead of 'which' using the builtin 'command -v'
sudo "$(command -v python)" traffic_watch.py --port 5000 -ip 127.0.0.1 --threshold_period=1

# kill the flask webserver
killall flask
