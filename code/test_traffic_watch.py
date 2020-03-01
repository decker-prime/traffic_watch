import collections
import time
from unittest import TestCase

from tqdm import trange

from traffic_watch import TrafficAlert


class Test(TestCase):
    """
    This class is for testing the TrafficAlert functionality. The
    alert_period, (the time over which the alert is doing its average),
    is shortened from 120 seconds to 4 seconds so the test suite can run in a
    reasonable time.
    """
    # period is in seconds. Can be lengthened if desired
    alert_period = 4
    # number of avg packets over which the alert should occur
    alert_threshold = 8

    def test_traffic_alert_no_traffic(self):
        alert = TrafficAlert()
        test_traffic = collections.deque()
        alert.traffic_alert(test_traffic, self.alert_threshold,
                            self.alert_period)
        self.assertFalse(alert.alert_engaged)

    def test_traffic_alert_below_threshold(self):
        alert = TrafficAlert()
        test_traffic = collections.deque()
        for i in range(self.alert_threshold - 1):
            test_traffic.append({'time': time.time(),
                                 'src_ip': '0.0.0.0',
                                 'path': '/'})
        alert.traffic_alert(test_traffic, self.alert_threshold,
                            self.alert_period)
        self.assertFalse(alert.alert_engaged)

    def test_traffic_alert_above_threshold(self):
        alert = TrafficAlert()
        test_traffic = collections.deque()
        base_rate = (self.alert_threshold + 1)
        for i in range(base_rate):
            test_traffic.append({'time': time.time(),
                                 'src_ip': '0.0.0.0',
                                 'path': '/'})
        alert.traffic_alert(test_traffic, self.alert_threshold,
                            self.alert_period)
        self.assertTrue(alert.alert_engaged)

    def test_traffic_alert_shuts_off_after_alert(self):
        alert = TrafficAlert()
        test_traffic = collections.deque()
        for i in range(self.alert_threshold + 1):
            test_traffic.append({'time': time.time(),
                                 'src_ip': '0.0.0.0',
                                 'path': '/'})
        alert.traffic_alert(test_traffic, self.alert_threshold,
                            self.alert_period)
        self.assertTrue(alert.alert_engaged)

        # sleep until the alert period has elapsed
        for i in trange(0, 50, desc="Waiting for alert period to elapse..."):
            time.sleep((self.alert_period + 1) / 50)

        # simulate the next traffic alert update from the scheduler...
        alert.traffic_alert(test_traffic, self.alert_threshold,
                            self.alert_period)
        self.assertFalse(alert.alert_engaged)
