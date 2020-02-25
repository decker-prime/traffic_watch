#!/usr/bin/python3

import pprint
import psutil
from scapy.layers.http import HTTP, HTTPRequest

from scapy.all import *

loopback_buffer = set()

def get_interfaces():
    return psutil.net_if_addrs()

def the_header(packet):
    #print("---",flush=True)

    ''' 
    check for loopback - if the packet source is loopback, each packet
     goes through this callback twice - once for the 'transmission' on the
     loopback, and once for the 'reception'. Presently checking that the IP
     addresses for the src and dst are the same. 
    '''
    if packet.getlayer(IP).fields['src'] == packet.getlayer(IP).fields['dst']:
        # using a set and packet hashing to eliminate the duplicates - 
        # hash the packet and see if it already exists in our set. If it doesn't,
        # add it to the set and return. If it does, discard the one in the set
        # and move on with tracking the 'received' packet.
        if str(packet.layers) not in loopback_buffer:
            loopback_buffer.add(str(packet.layers))
            return
        else:
            loopback_buffer.discard(str(packet.layers))

    fields = packet.getlayer(HTTPRequest).fields
#    pprint.pprint(fields, indent=4)
    pprint.pprint(fields['Method'].decode('utf-8') + " " + 
            fields['Path'].decode('utf-8'), indent=4)

#conf.L3socket=L3RawSocket

if __name__ == '__main__':
    # We can't rely upon using scapy.layers.http (or the
    # older scapy_http) because it only recognizes http 
    # traffic to port 80 or 8080. (see https://github.com/invernizzi/scapy-http/blob/master/scapy_http/http.py#L260 ) 
    bind_layers(TCP,HTTP, dport=5000)
    bind_layers(TCP,HTTP, sport=5000)

    interfaces = get_interfaces()

    #sniff(prn=the_header, iface='lo', store=0, lfilter=lambda x: x.haslayer(HTTPRequest))
    sniff(prn=the_header, iface=interfaces, store=0, lfilter=lambda x: x.haslayer(HTTPRequest))
    #sniff(prn=the_header, iface='lo', store=0, filter='dst port 5000')
    #sniff(prn=the_header,  filter="tcp", store=0)
    #sniff(session=TCPSession, prn=the_header, iface='lo', filter="tcp", store=0)

