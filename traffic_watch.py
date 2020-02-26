#!/usr/bin/python3

import argparse
import psutil
from functools import partial
from multiprocessing import Process, Queue, Pipe
import multiprocessing
import time

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from pandas import DataFrame
from scapy.all import sniff, bind_layers, IP, TCP
from scapy.layers.http import HTTP, HTTPRequest

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

    fields = packet.getlayer(HTTPRequest).fields
    section = fields['Path'].decode('utf-8').split("/")
    
    if len(section)>0:
        section = f'/{section[1]}'
    else:
        section = '/'

    comm_queue.put({'time':recv_time
                    ,'src_ip':packet.getlayer(IP).getfieldval('src')
                    ,'path':section
                    })

def recent_activity(records, threshold_secs=10):
    now = time.time()
    # This was originally a list comprehension, but since the records are in
    # time order, breaking the iteration at the time threshold is easier to
    # read in this format
    records_to_check = []
    for i in reversed(records):
        if i['time'] > now - threshold_secs:
            records_to_check.append(i)
        else:
            break
    
    if len(records_to_check) > 0:
        df = DataFrame(records_to_check)
        vals = df.groupby(['path']).size().sort_values(ascending=False)
        
        message = "Most popular section"
        message += "s: " if len(vals)> 1 else ": "

        for section, hits in zip(vals.index, vals.values):
            message += f'{section}: {hits} '
            message += "hits, " if hits > 1 else "hit, "
        
        message += f'{len(records_to_check) / threshold_secs} requests/sec'
    else:
        message = "No recent activity..."

    print(message, end='\r', flush=True)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description='This program monitors and relates ' +
                            'interesting HTTP traffic stats on your box')
    parser.add_argument('--port', '-p', type=int, help="The port to monitor", default=8080)
    args = parser.parse_args()

    if args.port != 80 and args.port != 8080:
            # scapy.layers.http (or the older scapy_http) only recognize http
            # traffic to port 80 or 8080.  So if the user chose another port,
            # we have to bind it here for the packet inspection to work (see
            # https://github.com/invernizzi/scapy-http/blob/master/scapy_http/http.py#L260) 
            bind_layers(TCP,HTTP, dport=args.port) 
            bind_layers(TCP,HTTP, sport=args.port)

    traffic_records = []

    scheduler = BackgroundScheduler()
    scheduler.add_job(recent_activity, 'interval', seconds=10, args=(traffic_records,))

    # this is the queue for receiving info from the network-sniffing subprocess
    incoming_data_queue = multiprocessing.Queue()

    sniffer = Process(target=run_sniffer, args=(args.port,incoming_data_queue))
    sniffer.daemon = True
    sniffer.start()
    scheduler.start()
    
    #counter = 0
    while True:
            new_traffic = incoming_data_queue.get()
            traffic_records.append(new_traffic)
            #print(new_traffic, end='\r', flush=True)
    #        counter  = counter+1
    #        if counter > 4:
    #            break

    #recent_activity(traffic_records) 

'''
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
'''
