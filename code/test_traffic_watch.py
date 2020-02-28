import time
from unittest import TestCase
import collections
from traffic_watch import TrafficAlert

class Test(TestCase):

    alert_period = 4  # in seconds so tests finish in reasonable time
    alert_threshold = 8  # packets

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
        for i in range(base_rate * self.alert_period + 1):
            test_traffic.append({'time': time.time(),
                                 'src_ip': '0.0.0.0',
                                 'path': '/'})
        alert.traffic_alert(test_traffic, self.alert_threshold,
                            self.alert_period)
        self.assertTrue(alert.alert_engaged)
