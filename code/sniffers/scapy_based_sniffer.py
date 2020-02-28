import time
from functools import partial

import psutil
from scapy.all import sniff, IP, TCP, bind_layers
from scapy.layers.http import HTTPRequest, HTTP


class ScapySniffer:
    loopback_buffer = set()

    def run_sniffer(self, port_number, queue):

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
