from sniffers import bare_socket_based_sniffer
from sniffers import scapy_based_sniffer


def get_sniffer(name):
    """
    A simple factory - given a string it hands back the appropriate backend
    packet sniffer.
    @param name: one of 'scapy' for the scapy-based backend, and 'socket' for
        bare-bone but much faster hand implementation.
    @return: a packet sniffer
    """
    if name == "scapy":
        return scapy_based_sniffer.ScapySniffer()
    elif name == "socket":
        return bare_socket_based_sniffer.BareSocketSniffer()
    else:
        raise NotImplementedError(f"Unknown backend, {name}, please choose"
                                  " 'scapy' or 'socket'")
