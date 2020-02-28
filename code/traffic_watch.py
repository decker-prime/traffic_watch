#!/usr/bin/python3

import argparse
import collections
import multiprocessing
import time
from multiprocessing import Process

from apscheduler.schedulers.background import BackgroundScheduler
from pandas import DataFrame
from scapy.all import bind_layers, TCP
from scapy.layers.http import HTTP
import sniffers

# in seconds
RECORD_RETENTION_PERIOD = 600

import sys
import pdb


class ForkedPdb(pdb.Pdb):
    """A Pdb subclass that may be used
    from a forked multiprocessing child

    """

    def interaction(self, *args, **kwargs):
        _stdin = sys.stdin
        try:
            sys.stdin = open('/dev/stdin')
            pdb.Pdb.interaction(self, *args, **kwargs)
        finally:
            sys.stdin = _stdin


def recent_activity(records, threshold_secs=10):
    records_to_check, _ = get_last_n_seconds_records(records, threshold_secs)

    if len(records_to_check) > 0:
        df = DataFrame(records_to_check)
        vals = df.groupby(['path']).size().sort_values(ascending=False)

        message = "Most popular section"
        message += "s: " if len(vals) > 1 else ": "

        for section, hits in zip(vals.index, vals.values):
            message += f'{section}: {hits} '
            message += "hits, " if hits > 1 else "hit, "

        message += f'{len(records_to_check) / threshold_secs} requests/sec'
    else:
        message = "No recent activity..."

    print(message, end='\r', flush=True)


def get_last_n_seconds_records(records, n_secs):
    """
        Returns a list of records that were received from now to n seconds ago.

    @param records: built on a collections.deque but will work an any iterable
                    containing objects with a 'time' value.
    @type n_secs: float
    @param n_secs: number of seconds in the past to include in the
            output.
    @return: (list, when) The list of the events, newest to oldest, and the
            time that was used for t0 or 'now', so calling methods can know at
            what point in time the search backward began.
    """
    # print(f"{len(records)}")
    records_to_check = []
    now = time.time()
    # This was originally a list comprehension, but since the records are in
    # reverse time order, breaking the iteration at the time threshold is
    # easier to read in this format
    for i in reversed(records):
        if i['time'] > now - n_secs:
            records_to_check.append(i)
        else:
            break
    return records_to_check, now


def record_cleanup(records, retention_period):
    now = time.time()
    while len(records) > 0 and records[0]['time'] < now - retention_period:
        records.popleft()


class TrafficAlarm:
    alarm_engaged = False

    def traffic_alarm(self, records, alert_threshold, alert_period):
        recs, when = get_last_n_seconds_records(records, alert_period)
        num_records = len(recs)

        if num_records >= alert_threshold:
            if not self.alarm_engaged:
                self.alarm_engaged = True
                msg_time = time.strftime('%a, %d %b %Y %H:%M:%S',
                                         time.localtime(when))
                print(
                    f"High traffic generated an alert - hits = {num_records} " +
                    f"triggered at {msg_time}", flush=True)
        else:
            if self.alarm_engaged:
                self.alarm_engaged = False
                msg_time = time.strftime('%a, %d %b %Y %H:%M:%S',
                                         time.localtime(when))
                print(f"High traffic alert recovered at {msg_time}", flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='This program monitors and relates ' +
                    'interesting HTTP traffic stats on your box')
    parser.add_argument('--port', '-p', type=int, help="The port to monitor",
                        default=8080)
    parser.add_argument('--traffic_threshold', '-m', type=int,
                        help="The alert threshold - this number of average"
                             "packets over the 'threshold_period' period will "
                             "cause an alert to be displayed to the user.",
                        default=50)
    parser.add_argument('--threshold_period', type=float,
                        help="The alert threshold period - this the amount of "
                             "time over which the 'traffic_threshold' is "
                             "measured. In minutes, defaults to two minutes.",
                        default=2)
    parser.add_argument('--backend', '-b',
                        help="which backend packet sniffer to use, choices "
                             "are 'scapy' which is based on the popular "
                             "framework, or 'socket' which is hand written "
                             "but much faster, (but potentially less stable). "
                             "default: socket",
                        default='socket')
    args = parser.parse_args()

    port = args.port
    traffic_alarm_thresh = args.traffic_threshold
    alarm_period = args.threshold_period * 60  # cmd line arg is in minutes
    backend = args.backend

    traffic_records = collections.deque()

    scheduler = BackgroundScheduler()
    scheduler.add_job(recent_activity, 'interval', seconds=10,
                      args=(traffic_records,))

    trfc_alarm = TrafficAlarm()
    scheduler.add_job(trfc_alarm.traffic_alarm, 'interval', seconds=1,
                      args=(
                          traffic_records, traffic_alarm_thresh, alarm_period))

    scheduler.add_job(record_cleanup, 'interval', seconds=10,
                      args=(traffic_records, RECORD_RETENTION_PERIOD))

    # this is the queue for receiving info from the network-sniffing subprocess
    incoming_data_queue = multiprocessing.Queue()

    sniffer = sniffers.get_sniffer(backend)
    snifferProcess = Process(target=sniffer.run_sniffer,
                             args=(port, incoming_data_queue))
    snifferProcess.daemon = True
    snifferProcess.start()
    scheduler.start()

    # counter = 0
    while True:
        new_traffic = incoming_data_queue.get()
        traffic_records.append(new_traffic)
        # print(new_traffic, end='\r', flush=True)
        # counter = counter+1
        # if counter > 4:
        #    break

    # recent_activity(traffic_records)
