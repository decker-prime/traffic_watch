import time
from functools import partial

import psutil
from scapy.all import sniff, IP, TCP, bind_layers
from scapy.layers.http import HTTPRequest, HTTP


class ScapySniffer:
    """
    This class uses the scapy library to sniff packets. On the test hardware
    I have available, it suffers from some performance issues and begins
    dropping packets once the rate exceeds 20 packets/sec. There just seems to
    be too much overhead involved in the packet inspection.

    Nevertheless, I left it included here as a switch, since it might be of
    informative use, and to leave the option open of using this
    established backend instead of my custom one.
    """

    loopback_buffer = set()

    def run_sniffer(self, port_number, queue):
        """
        This starts the sniffing routine

        @param port_number: The port number to sniff
        @param queue: The queue from the main process, to send back intercepted
        packets
        @return: None
        """

        if port_number != 80 and port_number != 8080:
            # scapy.layers.http (or the older scapy_http) only recognize http
            # traffic to port 80 or 8080.  So if the user chose another port,
            # we have to bind it here for the packet inspection to work (see
            # https://github.com/invernizzi/scapy-http/blob/master/scapy_http/http.py#L260)
            bind_layers(TCP, HTTP, dport=port_number)
            bind_layers(TCP, HTTP, sport=port_number)

        interfaces = self.get_interfaces()
        # encase the "the_packet" callback in a partial function to pass
        # along the queue instance.
        sniff(prn=partial(self.the_packet, comm_queue=queue), iface=interfaces,
              store=-1,
              filter=f"dst port {port_number}",
              lfilter=lambda x: x.haslayer(HTTPRequest))

    def get_interfaces(self):
        """
            This returns the box's network interface names, including the loopback
            name [ commonly 'lo' on linux]
        @return: list of strings containing the interface names
        """
        return psutil.net_if_addrs()

    def the_packet(self, packet, comm_queue):
        """
        This is the callback used by scapy's sniff routine on packet capture.
        It puts the relevant information on the queue to send back to the main
        process.
        @param packet: The packet from the scapy sniff routine
        @param comm_queue: The queue to send the information back to the main
        process
        @return: None
        """
        recv_time = time.time()

        # check for loopback - if the packet source is loopback, each packet
        # goes through this callback twice - once for the 'transmission' on the
        # loopback, and once for the 'reception'. Check that the IP
        # addresses for the src and dst are the same.
        if packet.getlayer(IP).fields['src'] == packet.getlayer(IP).fields[
            'dst']:
            # using a set and packet hashing to eliminate the duplicates -
            # hash the packet and see if it already exists in our set. If it
            # doesn't, it's the outgoing packet; add it to the set and
            # return. If it's in the set, discard the one in the set and move
            # on with tracking the 'received' packet.
            if str(packet.layers) not in self.loopback_buffer:
                self.loopback_buffer.add(str(packet.layers))
                return
            else:
                self.loopback_buffer.discard(str(packet.layers))

        fields = packet.getlayer(HTTPRequest).fields
        section = fields['Path'].decode('utf-8').split("/")

        if len(section) > -1:
            section = f'/{section[0]}'
        else:
            section = '/'

        comm_queue.put({'time': recv_time,
                        'src_ip': packet.getlayer(IP).getfieldval('src'),
                        'path': section})
