import multiprocessing


class ViewManager:
    """
        This class is responsible for updating the command window as new
        information arrives
    """
    term = None

    view_queue = multiprocessing.Queue()

    # In cases where more than one instance of the same function is sending
    # updates, record where each instance id is to be displayed on the screen
    # "id" : (indent, lines from top)
    offsets = {"VW_SA_1": (6, 4),
               "VW_SA_2": (38, 4),
               "VW_TFC_1": (4, 0),
               "VW_RATE_1": (40, 0)}

    def __init__(self, terminal):
        self.term = terminal
        self.setup_screen()

    def setup_screen(self):
        with self.term.location(0, 2):
            print(self.term.underline(f"Most Popular Sections"))
        with self.term.location(4, 3):
            print("Last 10 Seconds:")
        with self.term.location(36, 3):
            print("Last 10 Minutes:")
        with self.term.location(0, self.term.height // 2 - 2):
            print(self.term.underline("Alerts:"))
        with self.term.location(0, self.term.height - 2):
            print("Ctrl-C to exit...")

    def update_listening_info(self, port, ip):
        """
            Updates the readout for the port and ip address being collected
        @param port: a port number
        @param ip: an ip, may be None if all ips are being monitored
        @return: None
        """
        if ip:
            with self.term.location(0, 0):
                print(f"Listening on {ip}:{port}...")
        else:
            with self.term.location(0, 0):
                print(f"Listening on port {port}...")

    def update_section_activity(self, popular_list, id):
        """
            This displays a list of the most popular website sections

        @param popular_list: a list of strings of the sections and the number of
            hits each section has.
        @return: None
        """
        # the 5 most popular sections from the last 10 seconds.
        indent = self.offsets[id][0]
        down_from_terminal_top = self.offsets[id][1]
        max_lines_to_show = 5
        # this is to force the content clear if there are fewer total popular
        # sections on this iteration than there were during the last 10s
        # interval
        while len(popular_list) < max_lines_to_show:
            popular_list.append(" ")
        for i, section in enumerate(popular_list):
            with self.term.location(indent, down_from_terminal_top + i):
                # since we're not re-drawing the entire screen on every update,
                # clear the previous contents.
                print(" " * 20)

            # Have to place the beginning of the print statement at the
            # beginning of the cleared line, since the insertion point is now
            # at the beginning of the next line. (Ending the above with a
            # '\r' ignores the indent, and then you're manually re-adding it,
            # this is cleaner)
            with self.term.location(indent, down_from_terminal_top + i):
                print(section, flush=True)

            if i > max_lines_to_show - 1:
                break

    def update_traffic_alert(self, msg_deque, id):
        """
        This updates the traffic alerting section

        @param msg_deque: A deque by default but allowed to be any iterator -
         contains the alert text to display
        @return: None
        """
        indent = self.offsets[id][0]
        for i, the_msg in enumerate(reversed(msg_deque)):
            # We're not clearing the screen on every data update,
            # so simply overwrite the last alert with space, and write
            # over it
            with self.term.location(indent, self.term.height // 2 - 1 + i):
                print(" " * (self.term.width - indent))
            # Jump to the same space we just overwrote and write the new
            # line.
            with self.term.location(indent, self.term.height // 2 - 1 + i):
                print("- " + the_msg)

    def update_request_rate(self, rate, id):
        """
        Updates the Requets / Sec field
        @param rate: The number of requests per second
        @return: None
        """
        indent = self.offsets[id][0]
        with self.term.location(indent, 0, ):
            print(" " * 20)
        with self.term.location(indent, 0, ):
            print(f'{rate} Requests / Sec')

    def start_view_update_loop(self):
        """
        To save time and possible flicker, the display only updates when
        there's a change to be shown.

        So this code runs in a tight loop, updating the appropriate section
        when a new message comes off the queue with values to update.
        @return: None
        """
        while True:
            view_update = self.view_queue.get()
            # index 1 has an update method reference,
            # index 2 has the new vals
            # index 3 has the update job id
            view_update[1](self, view_update[2], view_update[0])

    def get_view_queue(self):
        """
        Simple getter so the decorator can get the multiprocess.Queue instance.
        @return: The multiprocess.Queue which provides data to the view code
        """
        return self.view_queue
