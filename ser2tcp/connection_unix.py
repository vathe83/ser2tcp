"""Connection Unix"""

import ser2tcp.connection as _connection


class ConnectionUnix(_connection.Connection):
    """Unix connection"""
    def __init__(self, connection, dev, log=None):
        super().__init__(connection, log)
        self._input_source = dev
        self._log.info("Client connected: %s UNIX", self._socket.getsockname())

    @staticmethod
    def list_pull_first(data):
        """get first entry from array"""
        dat = data[0]
        del data[0]
        return dat

    def on_received(self, data):
        """Received data from client"""
        if data:
            print(data)
            self._input_source.send(data)
