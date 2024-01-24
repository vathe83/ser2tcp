"""Server"""

import logging as _logging
import socket as _socket
import ser2tcp.server as _server


class UnixSocketProxy():
    """Unix socket connection manager"""
    # PARITY_CONFIG = {
    #     'NONE': _serial.PARITY_NONE,
    #     'EVEN': _serial.PARITY_EVEN,
    #     'ODD': _serial.PARITY_ODD,
    #     'MARK': _serial.PARITY_MARK,
    #     'SPACE': _serial.PARITY_SPACE,
    # }
    # STOPBITS_CONFIG = {
    #     'ONE': _serial.STOPBITS_ONE,
    #     'ONE_POINT_FIVE': _serial.STOPBITS_ONE_POINT_FIVE,
    #     'TWO': _serial.STOPBITS_TWO,
    # }
    # BYTESIZE_CONFIG = {
    #     'FIVEBITS': _serial.FIVEBITS,
    #     'SIXBITS': _serial.SIXBITS,
    #     'SEVENBITS': _serial.SEVENBITS,
    #     'EIGHTBITS': _serial.EIGHTBITS,
    # }

    def __init__(self, config, log=None):
        self._log = log if log else _logging.Logger(self.__class__.__name__)
        self._input_source = None
        self._servers = []
        self._input_source_config = config['input_source']  # self.fix_input_source_config(config['input_source'])
        self._log.info(
            "Unix socket: %s %d",
            self._input_source_config['port'],
            self._input_source_config['baudrate'])
        for server_config in config['servers']:
            self._servers.append(_server.Server(server_config, self, log))

    # def fix_input_source_config(self, config):
    #     """Fix unix socket configuration"""
    #     if 'parity' in config:
    #         for key, val in self.PARITY_CONFIG.items():
    #             if config['parity'] == key:
    #                 config['parity'] = val
    #     if 'stopbits' in config:
    #         for key, val in self.STOPBITS_CONFIG.items():
    #             if config['stopbits'] == key:
    #                 config['stopbits'] = val
    #     if 'bygesize' in config:
    #         for key, val in self.STOPBITS_CONFIG.items():
    #             if config['bytesize'] == key:
    #                 config['bytesize'] = val
    #     return config

    def __del__(self):
        self.close()

    def connect(self):
        """Connect to serial port"""
        if not self._input_source:
            try:
                # serial
                # self._input_source = _serial.Serial(**self._input_source_config)
                self._input_source = _socket.socket(_socket.AF_UNIX,
                                                    _socket.SOCK_STREAM)
                self._input_source.connect(self._input_source_config['port'])
            except FileNotFoundError as err:
                self._log.warning(err)
                return False
            self._log.info(
                "Unix socket %s connected", self._input_source_config['port'])
        return True

    def has_connections(self):
        """Check if there are any active connections"""
        for server in self._servers:
            if server.has_connections():
                return True
        return False

    def disconnect(self):
        """Disconnect unix socket, but if there are no active connections"""
        if self._input_source and not self.has_connections():
            self._input_source.close()
            self._input_source = None
            self._log.info(
                "Unix socket %s disconnected",
                self._input_source_config['port'])

    def close(self):
        """Close socket and all connections"""
        while self._servers:
            self._servers.pop().close()
        self.disconnect()

    def sockets(self):
        """Return all sockets from this server"""
        sockets = []
        for server in self._servers:
            sockets += server.sockets()
        if self._input_source:
            sockets.append(self._input_source)
        return sockets

    def send_to_connections(self, data):
        """Send data to all connections"""
        for server in self._servers:
            server.send(data)

    def socket_event(self, read_sockets):
        """Process sockets with read event"""
        for server in self._servers:
            server.socket_event(read_sockets)
        if self._input_source and self._input_source in read_sockets:
            try:
                data = self._input_source.recv(4096)
                self._log.debug("(%s): %s", self._input_source_config['port'],
                                data)
                self.send_to_connections(data)
            except (OSError, _socket.error) as err:
                self._log.warning(err)
                for server in self._servers:
                    server.close_connections()
                self.disconnect()
                return

    def send(self, data):
        """Send data to unix socket"""
        if self._input_source:
            self._input_source.sendall(data)
