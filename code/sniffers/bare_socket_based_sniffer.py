import re
import socket
import time
from struct import unpack


class BareSocketSniffer:
    """
    I coded this packet sniffer entirely in the python networking api, to
    skip third-party libraries. It runs fast enough on my test hardware to
    capture >1,000 packets per second, and so is the preferred method of
    capture for this app.
    """

    # this regex will be used to determine if the packet inside the tcp packet
    # appears to be HTTP
    http_payload_re = re.compile(
        r"^(?:OPTIONS|GET|HEAD|POST|PUT|DELETE|TRACE|CONNECT) "
        r"(.+?) "
        r"HTTP/\d\.\d"
    )

    def run_sniffer(self, ip, dest_port, queue=None):
        """
        This is the entry point for this sniffer.

        @param dest_port: The port we're interested in
        @param ip: The destination ip to listen for. If this is 'None', all
        messages to to any ips will be logged, (so long as the port number
        matches)
        @param queue: The queue which sends back packet info to the main process
        @return: None
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                              socket.IPPROTO_TCP)
        except socket.error as e:
            print(f'Problem creating the socket, permissions? ' +
                  'Error {e[0]}, {e[1]}')
            raise e

        while True:
            # Give me everything
            packet, addr = s.recvfrom(0xffff)
            # Timestamp it
            recv_time = time.time()

            # take first 20 characters for the ip header
            ip_header = packet[0:20]

            # This is kind of ugly but it's python's way of packing and
            # unpacking binary data, for converting between python values and
            # C structs. https://docs.python.org/3.7/library/struct.htm for more.
            # Parsing just the IP header... see RFC791
            ipheader_fields = unpack('!BBHHHBBH4s4s', ip_header)

            version_ihl = ipheader_fields[0]
            version = version_ihl >> 4
            # the ip header length in 32 bit words
            ihl = version_ihl & 0xF

            # bytes are easier to think about
            ipheader_length = ihl * 4

            # ipheader_fields[5] is ttl, not useful for now
            protocol = ipheader_fields[6]

            # The TCP protocol's magic number is 6, (see RFC 790)
            # skip this packet if it doesn't contain TCP
            if protocol != 6:
                continue

            s_addr = socket.inet_ntoa(ipheader_fields[8])
            d_addr = socket.inet_ntoa(ipheader_fields[9])
            # toss packets with ip destinations not matching our filter, if a
            # filter was passed...
            if ip and ip != d_addr:
                continue

            tcp_header = packet[ipheader_length:ipheader_length + 20]

            # rfc793 for tcp header packing
            tcp_header_fields = unpack('!HHLLBBHHH', tcp_header)

            packet_source_port = tcp_header_fields[0]
            packet_dest_port = tcp_header_fields[1]
            if packet_dest_port != dest_port:
                continue

            # for debugging, uncomment this to see responses also
            # if packet_dest_port == dest_port or packet_source_port == dest_port:
            #     continue

            sequence = tcp_header_fields[2]
            acknowledgement = tcp_header_fields[3]
            doff_reserved = tcp_header_fields[4]
            tcp_header_length = doff_reserved >> 4
            total_header_size = ipheader_length + tcp_header_length * 4

            data_size = len(packet) - total_header_size

            if data_size == 0:
                continue

            # Debugging code to show packet details
            # print('Version : ' + str(version) + ' IP Header Length : ' +
            #    str(ihl) + ' Protocol : ' + str(protocol) + ' Source Address : ' +
            #    str( s_addr) + ' Destination Address : ' + str(d_addr))
            #
            # print( 'Source Port : ' + str(packet_source_port) + ' Dest Port : '
            #    + str( packet_dest_port) + ' Sequence Number : ' + str(sequence) +
            #    'Acknowledgement : ' + str( acknowledgement) + ' TCP header '+
            #    'length : ' + str(tcp_header_length))

            # get data from the packet
            data = packet[total_header_size:]

            try:
                # if it's encrypted this won't work, obviously
                payload_data = data.decode('utf-8')
            except UnicodeDecodeError:
                print("issue decoding data in packet, skipping")
                continue

            # see if the data looks like HTTP
            result = self.http_payload_re.search(payload_data)
            if not result or len(result.groups()) == 0:
                continue

            # extract the 'section'
            section = result.group(1).split('/')
            if len(section) > 2:
                # this is the form /foo/index.html, so the split looks like
                # ['', 'foo', 'index.html']
                section = f'/{section[1]}'
            else:
                # this is the form /index.html
                section = '/'

            if queue:
                queue.put({'time': recv_time,
                           'src_ip': s_addr,
                           'path': section})
            else:
                print(data.decode('utf-8'))


# For testing purposes, this may be started by itself
if __name__ == '__main__':
    sniffer = BareSocketSniffer()
    sniffer.run_sniffer(dest_port=5000)
