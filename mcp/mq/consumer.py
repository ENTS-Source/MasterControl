import pika
import logging

class MqConsumer:
    def __init__(self, queueName, amqpUrl, callback):
        self._logger = logging.getLogger(__name__)
        self._callback = callback
        self._queueName = queueName
        self._amqpUrl = amqpUrl
        self._stopping = False
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
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)
        self._channel.basic_consume(self.on_message, self._queueName)

    def on_consumer_cancelled(self, method_frame):
        self._logger.warning("MQ server cancelled consumer")
        if self._channel:
            self._channel.close()

    def on_channel_closed(self, channel, reply_code, reply_text):
        if self._stopping:
            return
        self._logger.warning("Channel to MQ server was closed, reconnecting")
        self._connection.close()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        self._callback(body)
        self._channel.basic_ack(basic_deliver.delivery_tag)

    def stop(self):
        self._stopping = True
        if self._channel:
            self._channel.close()
