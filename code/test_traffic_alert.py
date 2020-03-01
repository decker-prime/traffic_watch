import collections
import time
from unittest import TestCase

from tqdm import trange

from traffic_watch import TrafficAlert


class TestTrafficAlert(TestCase):
    """
    This class is for testing the TrafficAlert functionality. The
    alert_period, (the time over which the alert is doing its average),
    is shortened from 120 seconds to 4 seconds so the test suite can run in a
    reasonable time.
    """
    # period is in seconds. It can be lengthened if desired
    alert_period = 4
    # number of avg packets over which the alert should occur
    alert_threshold = 8

    def test_traffic_alert_no_traffic(self):
        """
        This tests the case where there's no traffic, so there shouldn't be
        any alerting
        """
        alert = TrafficAlert()
        test_traffic = collections.deque()
        alert.traffic_alert(test_traffic, self.alert_threshold,
                            self.alert_period)
        self.assertFalse(alert.alert_engaged)

    def test_traffic_alert_below_threshold(self):
        """
        This tests the case where there is traffic, but it remains below the
        alert levels. The alert should remain disengaged
        """
        alert = TrafficAlert()
        test_traffic = collections.deque()
        # fake up some traffic
        for i in range(self.alert_threshold*self.alert_period - 1):
            test_traffic.append({'time': time.time(),
                                 'src_ip': '0.0.0.0',
                                 'path': '/'})
        # trigger the alert check, like the scheduler does
        alert.traffic_alert(test_traffic, self.alert_threshold,
                            self.alert_period)
        self.assertFalse(alert.alert_engaged)

    def test_traffic_alert_above_threshold(self):
        """
        This test checks that the alert fires properly when the amount of
        traffic exceeds the threshold
        """
        alert = TrafficAlert()
        test_traffic = collections.deque()
        base_rate = (self.alert_threshold * self.alert_period + 1)
        # fake up some traffic
        for i in range(base_rate):
            test_traffic.append({'time': time.time(),
                                 'src_ip': '0.0.0.0',
                                 'path': '/'})
        # trigger the alert check, like the scheduler does
        alert.traffic_alert(test_traffic, self.alert_threshold,
                            self.alert_period)
        self.assertTrue(alert.alert_engaged)

    def test_traffic_alert_shuts_off_after_alert(self):
        """
        This test checks that the alert successfully returns to a non-alert
        state after the alert traffic conditions clear
        """
        alert = TrafficAlert()
        test_traffic = collections.deque()
        # fake up some traffic
        for i in range(self.alert_threshold*self.alert_period + 1):
            test_traffic.append({'time': time.time(),
                                 'src_ip': '0.0.0.0',
                                 'path': '/'})
        # trigger the alert check, like the scheduler does
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
