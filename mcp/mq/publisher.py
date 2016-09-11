import pika
import json
import logging

class MqPublisher:
    def __init__(self, exchangeName, amqpUrl):
        self._logger = logging.getLogger(__name__)
        self._exchangeName = exchangeName
        self._amqpUrl = amqpUrl
        self._stopping = False
        self._backlog = []
        self._channel = None
        self._connection = None

    def start(self):
        while(True):
            self._attempt_connection()

    def _attempt_connection(self):
        self._logger.info("Initiating connection...")
        if self._connection is None:
            self._connection = pika.SelectConnection(pika.URLParameters(self._amqpUrl),
                                                     on_open_callback=self.on_connection_open,
                                                     on_open_error_callback=self.on_connection_open_error,
                                                     on_close_callback=self.on_connection_error,
                                                     stop_ioloop_on_close=False)
        else:
            self._connection.connect()
        self._connection.ioloop.start()

    def on_connection_open(self, unused_connection):
        self._logger.info("Connection established")
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_connection_open_error(self, unused_connection, error_message):
        self._logger.warning("Failed to connect to MQ, reconnecting...")
        if (self._connection is not None):
            self._connection.ioloop.stop()
        self._connection = None
        self._attempt_connection()

    def on_connection_error(self, connection, reply_code, reply_text):
        if self._stopping:
            return
        self._logger.warning("Connection to MQ interrupted, reconnecting...")
        if (self._connection is not None):
            self._connection.ioloop.stop()
        #self._attempt_connection() # reconnection handled in start()

    def on_channel_open(self, channel):
        self._channel = channel
        self._channel.add_on_close_callback(self.on_channel_closed)
        localBacklog = self._backlog[:] # copy
        self._backlog = []
        self._logger.info("Processing backlog...")
        for item in localBacklog:
            self.publish(item)
            self._logger.info(item)
        self._logger.info("Backlog processed")

    def on_channel_closed(self, channel, reply_code, reply_text):
        if self._stopping:
            return
        self._logger.warning("Channel to MQ server was closed, reconnecting")
        self._connection.close()

    def publish(self, message):
        if self._channel is None or not self._channel.is_open:
            self._logger.warning("Channel not available, adding message to backlog")
            self._backlog.append(message)
            return
        self._logger.debug("Publishing message")
        self._channel.basic_publish(self._exchangeName, "", json.dumps(message))

    def stop(self):
        self._stopping = True
        if self._channel:
            self._channel.close()
