#!/usr/bin/python3

import argparse
import pprint
import psutil
from functools import partial
from scapy.layers.http import HTTP, HTTPRequest
from multiprocessing import Process, Queue, Pipe
import multiprocessing
import time
import pandas

from scapy.all import sniff, bind_layers, IP, TCP


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

loopback_buffer = set()

def run_sniffer(port_number, queue):
    interfaces = get_interfaces()

    # encase the callback in a partial function to pass along the queue instance. 
    sniff(prn=partial(the_packet,comm_queue=queue), iface=interfaces, store=0, 
                      filter=f"dst port {port_number}",
                      lfilter=lambda x: x.haslayer(HTTPRequest))

def get_interfaces():
    ''' This returns the box's network interface names, including the loopback
        name [ commonly lo on linux] ''' 
    return psutil.net_if_addrs()

def the_packet(packet, comm_queue):
    recv_time = time.time()
 
    # check for loopback - if the packet source is loopback, each packet
    # goes through this callback twice - once for the 'transmission' on the
    # loopback, and once for the 'reception'. Presently checking that the IP
    # addresses for the src and dst are the same. 
    if packet.getlayer(IP).fields['src'] == packet.getlayer(IP).fields['dst']:
        # using a set and packet hashing to eliminate the duplicates - hash the
        # packet and see if it already exists in our set. If it doesn't, it's
        # the outgoing packet; add it to the set and return. If it's in the
        # set, discard the one in the set and move on with tracking the
        # 'received' packet.
        if str(packet.layers) not in loopback_buffer:
            loopback_buffer.add(str(packet.layers))
            return
        else:
            loopback_buffer.discard(str(packet.layers))

    #ForkedPdb().set_trace()

    fields = packet.getlayer(HTTPRequest).fields
    #pprint.pprint(packet.getlayer(TCP).fields, indent=4)
    #pprint.pprint(fields, indent=4)
    
    comm_queue.put({'time':recv_time
                    ,'src_ip':packet.getlayer(IP).getfieldval('src')
                    ,'path':fields['Path'].decode('utf-8')
                    })

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description='This program monitors and relates ' +
                            'interesting HTTP traffic stats on your box')
    parser.add_argument('--port', '-p', type=int, help="The port to monitor", default=8080)
    args = parser.parse_args()

    if args.port != 80 and args.port != 8080:
            # scapy.layers.http (or the older scapy_http) only recognize http
            # traffic to port 80 or 8080.  So if the user chose something else,
            # we have to bind the other ports here for the packet inspection to
            # work (see
            # https://github.com/invernizzi/scapy-http/blob/master/scapy_http/http.py#L260) 
            bind_layers(TCP,HTTP, dport=args.port) 
            bind_layers(TCP,HTTP, sport=args.port)


    # this is the queue for receiving info from the network-sniffing subprocess
    incoming_data_queue = multiprocessing.Queue()

    sniffer = Process(target=run_sniffer, args=(args.port,incoming_data_queue))
    sniffer.daemon = True
    sniffer.start()
    
    traffic_records = []
    while True:
            new_traffic = incoming_data_queue.get()
            traffic_records.append(new_traffic)
            print(new_traffic, end='\r', flush=True)
    
