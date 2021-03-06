import logging
import socket
import random


class Connection(object):
    '''Statsd Connection

    :keyword host: The statsd host to connect to, defaults to `localhost`
    :keyword port: The statsd port to connect to, defaults to `8125`
    :keyword sample_rate: The sample rate, defaults to `1` (meaning always)
    :keyword disabled: Turn off sending UDP packets, defaults to ``False``
    '''

    default_host = 'localhost'
    default_port = 8125
    default_sample_rate = 1
    default_disabled = False

    @classmethod
    def set_defaults(cls, host='localhost', port=8125, sample_rate=1, disabled=False):
        cls.default_host = host
        cls.default_port = port
        cls.default_sample_rate = sample_rate
        cls.default_disabled = disabled

    def __init__(self, host=None, port=None, sample_rate=None, disabled=None):
        self._host = host or self.default_host
        self._port = int(port or self.default_port)
        self._sample_rate = sample_rate or self.default_sample_rate
        self._disabled = disabled or self.default_disabled
        self.logger = logging.getLogger('%s.%s'
            % (__name__, self.__class__.__name__))
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger.debug('Initialized connection to %s:%d with P(%.1f)',
            self._host, self._port, self._sample_rate)

    def send(self, data, sample_rate=None):
        '''Send the data over UDP while taking the sample_rate in account

        The sample rate should be a number between `0` and `1` which indicates
        the probability that a message will be sent. The sample_rate is also
        communicated to `statsd` so it knows what multiplier to use.
        '''
        if self._disabled:
            self.logger.debug('Connection disabled, not sending data')
            return False
        if sample_rate is None:
            sample_rate = self._sample_rate

        sampled_data = {}
        if sample_rate < 1:
            if random.random() <= sample_rate:
                # Modify the data so statsd knows our sample_rate
                for stat, value in data.iteritems():
                    sampled_data[stat] = '%s|@%s' % (data[stat], sample_rate)
        else:
            sampled_data = data

        try:
            for stat, value in sampled_data.iteritems():
                send_data = '%s:%s' % (stat, value)
                self.udp_sock.sendto(send_data, (self._host, self._port))
                return True
        except Exception, e:
            self.logger.exception('unexpected error %r while sending data', e)
            return False

    def __repr__(self):
        return '<%s[%s:%d] P(%.1f)>' % (
            self.__class__.__name__,
            self._host,
            self._port,
            self._sample_rate,
        )

