import psutil
import socket
from datetime import datetime


class SystemMonitor:

    @staticmethod
    def cpu():
        return round(psutil.cpu_percent(interval=0.1), 1)

    @staticmethod
    def ram():
        return round(psutil.virtual_memory().percent, 1)

    @staticmethod
    def disk():
        return round(psutil.disk_usage("/").percent, 1)

    @staticmethod
    def network_usage():

        net = psutil.net_io_counters()

        sent = net.bytes_sent / (1024 * 1024)

        recv = net.bytes_recv / (1024 * 1024)

        return round(sent, 1), round(recv, 1)

    @staticmethod
    def internet():

        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError:
            return False

    @staticmethod
    def current_time():

        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def current_date():

        return datetime.now().strftime("%d %b %Y")