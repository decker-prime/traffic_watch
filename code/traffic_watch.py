#!/usr/bin/python3

import argparse
import collections
import multiprocessing
import time
from multiprocessing import Process
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
from blessed import Terminal
from pandas import DataFrame

import sniffers
from view_manager import ViewManager

# in seconds
RECORD_RETENTION_PERIOD = 600

# This is the default requests / sec the alert at which point he traffic alert
# activates
DEFAULT_TRAFFIC_THRESHOLD_PER_SECOND = 20

# This lock is to prevent issues with the accessing the records data
lock = Lock()


class TrafficAlert:
    """
    This class handles the alerting for traffic over some threshold.
    """
    # This is the alert-in-progress indicator.
    alert_engaged = False

    # This deque contains the notifications that have happened, as well as
    # the notifications that are happening.
    msg_deque = collections.deque()

    def traffic_alert(self, records, alert_threshold, alert_period,
                      per_second=True):
        """
        This is the entry method for this Alert. The alert threshold may be
        specified as either avg messages/sec over the alert period, or total
        messages over the alert_period. It's a simple multiplication between
        the two values, but it's easier to be able to think about it from
        one perspective or the other.

        @param records: A collections.deque containing the request records
        @param alert_threshold: The threshold of messages above which to set the
        alert. It has two modes, depending on the state of the "per_second"
        argument:
            If per_second is True, this behaves as msgs/sec, which is to say,
             if set to 20 msg/sec, a 2 minute period would cause the Alert to
             fire if the average number of messages per second during that time
             is 20 msgs/sec, (or 2400 total messages)
            If per_second is False, this behaves as total number of messages
             during the time period to set the alert, so to get the same
             behavior as above, one would set this to 2400 messages total.
        @param alert_period: The time period over which to total the average.
        @param per_second: Boolean - changes the behavior of the alert_threshold
        argument, see above.
        @return: None
        """
        recs, when = get_last_n_seconds_records(records, alert_period)
        num_records = len(recs)

        msg = None
        if per_second:
            is_alert = num_records / alert_period >= alert_threshold
        else:
            is_alert = num_records >= alert_threshold

        if is_alert:
            if not self.alert_engaged:
                self.alert_engaged = True
                msg_time = time.strftime('%d %b %H:%M:%S',
                                         time.localtime(when))

                msg = f"High traffic generated an alert - hits = " + \
                      f"{num_records} " + \
                      f"triggered at {msg_time}"
        else:
            if self.alert_engaged:
                self.alert_engaged = False
                msg_time = time.strftime('%d %b %H:%M:%S',
                                         time.localtime(when))
                msg = f"High traffic alert recovered at {msg_time}"

        # To prevent the deque from growing forever, assume a max console
        # height of a big number, and delete the rows that have long fallen
        # off the bottom
        while len(self.msg_deque) > 500:
            self.msg_deque.popleft()

        if msg:
            self.msg_deque.append(msg)
        return self.msg_deque


def recent_section_activity(records, threshold_secs=10):
    """
    This method obtains the most popular website 'sections' in the last 10
    seconds, (or threshold_secs).
    @param records: An iterable collection with the request records
    @param threshold_secs: The number of seconds over which to collect the
    'most popular section' info.
    @return: None
    """
    records_to_check, _ = get_last_n_seconds_records(records, threshold_secs)

    popular_list = []
    if len(records_to_check) > 0:
        df = DataFrame(records_to_check)
        vals = df.groupby(['path']).size().sort_values(ascending=False)

        for section, hits in zip(vals.index, vals.values):
            message = f'{section}: {hits} '
            message += "hits" if hits > 1 else "hit"
            popular_list.append(message)
    else:
        popular_list.append("No activity in the last 10 seconds...")
    return popular_list


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
    records_to_check = []
    now = time.time()
    # This was originally a list comprehension, but since the records are in
    # reverse time order, since we need to break the iteration at a time
    # threshold, this format is much easier to read.
    with lock:
        for i in reversed(records):
            if i['time'] > now - n_secs:
                records_to_check.append(i)
            else:
                break
    return records_to_check, now


def record_cleanup(records, retention_period):
    """
    This job is to keep the records deque to a manageable length, so it doesn't
    grow forever.
    @param records: A collections.deque containing request records
    @param retention_period: This is treated like time.time()-retention period.
    Items older than this are discarded.
    @return: None
    """
    now = time.time()
    with lock:
        while len(records) > 0 and records[0]['time'] < now - retention_period:
            records.popleft()


def display(id, display_method):
    """
    This method is used as a python decorator, to link the monitoring functions
    to a queue which connects to the viewing code. This decouples the
    calculation jobs from the display thread.

    @param id: A unique ID for the wrapped method, so if two or more instances
     of the same method are sending updates to the view, that it can
     tell them apart.
    @param display_method: This is a reference to the actual view function.
     This could be further decoupled by using strings and reflection, but I
     don't want to pay the runtime cost on each update.
    @return: The wrapped function
    """

    def wrapper(func):
        myqueue = None

        def activity_call(*args, **kwargs):
            nonlocal myqueue
            if not myqueue:
                myqueue = view_manager.get_view_queue()

            output = func(*args, **kwargs)
            myqueue.put([id, display_method, output])
            return

        return activity_call

    return wrapper


traffic_alert = TrafficAlert()

# This section hooks the various profiling functions to their display
# counterparts. We could have just marked the functions directly, but then
# unit tests become a problem, because calling the function then requires
# the view to exist.
@display("VW_TFC_1", ViewManager.update_traffic_alert)
def display_traffic_alert(records, alert_threshold, alert_period,
                          per_second=True):
    return traffic_alert.traffic_alert(records, alert_threshold, alert_period,
                                       per_second)


@display("VW_RATE_1", ViewManager.update_request_rate)
def display_current_rate(records):
    len_records, _ = get_last_n_seconds_records(records, 1)
    return len(len_records)


@display("VW_SA_1", ViewManager.update_section_activity)
def display_recent_section_activity(records, threshold_secs=10):
    return recent_section_activity(records, threshold_secs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
                                     'This program monitors and relates ' +
                                     'interesting HTTP traffic stats on the box')

    parser.add_argument('--port', '-p', type=int, help="The port to monitor",
                        default=8080)

    parser.add_argument('-ip', type=str,
                        help="The ip to monitor. If "
                             "not provided, the sniffer will intercept all traffic "
                             "to any ip with the matching port number. Depending on "
                             "your network setup, ie: public wifi vs. wired switch "
                             "connection, this may or may not be what you want.",
                        default=None)

    parser.add_argument('--traffic_threshold_per_second', '-ts', type=int,
                        help="(this option is on by default and defaults to "
                             "20) The alert threshold - this number "
                             "of average packets PER SECOND over the "
                             "'threshold_period' period will cause an alert to "
                             "be displayed to the user. This option "
                             "and -tt cannot be used at the same time.")

    parser.add_argument('--traffic_threshold_total', '-tt', type=int,
                        help="The alert threshold - this number "
                             "of TOTAL PACKETS over the "
                             "'threshold_period' period will cause an alert to "
                             "be displayed to the user. This option and '-ts' "
                             "cannot be used at the same time.")

    parser.add_argument('--threshold_period', type=float,
                        help="(default: 2 minutes) The alert threshold period "
                             "- this the amount of time over which the "
                             "'traffic_threshold' is measured. In minutes,",
                        default=2)

    parser.add_argument('--backend', '-b',
                        help="(default: socket) which backend packet sniffer "
                             "to use, choices are 'scapy' which is based on "
                             "the popular framework, but has a limited ~15-20 "
                             "packets/sec listening speed, or 'socket' which "
                             "is hand written for this and much faster, "
                             "(but potentially less stable - I haven't had "
                             "any issues but your mileage may vary). ",
                        default='socket')
    args = parser.parse_args()

    # Pull the args into the appropriate variables
    port = args.port
    ip = args.ip

    if args.traffic_threshold_total:
        if args.traffic_threshold_per_second:
            parser.error("Cannot use options -tt and -ts at the same time")
        traffic_alarm_thresh = args.traffic_threshold_total
        thresh_avg_by_sec = False
    else:
        traffic_alarm_thresh = args.traffic_threshold_per_second
        if not traffic_alarm_thresh:
            traffic_alarm_thresh = DEFAULT_TRAFFIC_THRESHOLD_PER_SECOND
        thresh_avg_by_sec = True

    alarm_period = args.threshold_period * 60  # cmd line arg is in minutes
    backend = args.backend

    # This is a handle to the terminal session
    term = Terminal()

    # make sure the terminal is tall enough to display the data
    if term.height < 10:
        raise RuntimeError("Please resize your terminal window to be at least" +
                           " 10 rows tall.")

    # a deque that will hold the collected packet information
    traffic_records = collections.deque()

    # The scheduler mechanism. This calls the various background monitoring
    # jobs in this application
    scheduler = BackgroundScheduler()
    # The 'popular section' job
    scheduler.add_job(display_recent_section_activity, 'interval', seconds=10,
                      args=(traffic_records,))

    # The Traffic Alert check job
    scheduler.add_job(display_traffic_alert, 'interval', seconds=1,
                      args=(traffic_records,
                            traffic_alarm_thresh,
                            alarm_period,
                            thresh_avg_by_sec))

    # The record cleanup job, to control memory usage
    scheduler.add_job(record_cleanup, 'interval', seconds=10,
                      args=(traffic_records, RECORD_RETENTION_PERIOD))

    scheduler.add_job(display_current_rate, 'interval', seconds=1,
                      args=(traffic_records,))

    # this is the queue for receiving info from the network-sniffing subprocess
    incoming_data_queue = multiprocessing.Queue()

    # Putting the app inside this 'with' allows the client's terminal to be
    # restored to its former state on exit, even if the process doesn't exit
    # cleanly.
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        view_manager = ViewManager(term)
        view_manager.update_listening_info(port, ip)

        # Initialize a sniffer
        sniffer = sniffers.get_sniffer(backend)
        # Start the sniffer in a new process
        snifferProcess = Process(target=sniffer.run_sniffer,
                                 args=(ip, port, incoming_data_queue))
        snifferProcess.daemon = True
        snifferProcess.start()

        # Start the scheduler
        scheduler.start()

        # Start the view update loop
        viewProcess = Process(target=view_manager.start_view_update_loop)
        viewProcess.start()

        # Start the grabbing the incoming data off the queue
        while True:
            new_traffic = incoming_data_queue.get()
            with lock:
                traffic_records.append(new_traffic)
