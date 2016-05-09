from collections import namedtuple
import struct
import sys
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer
from tornado import gen
import logging
from tornado.log import LogFormatter


TLVCommand = namedtuple('TLVCommand', ['type', 'value'])


class LampError(Exception):
    pass


class LampHandler:
    '''Обработчик запросов управления фонарем.'''

    log = logging.getLogger('tornado.app.lamp')

    @classmethod
    def dispatch(cls, command):
        '''Обработать команду управления при помощи соответствующего метода.

        :param TLVCommand command: команда управления фонарем.

        '''
        # Поддерживаемые типы команд.
        commands = {
            b'\x12': cls.turn_on,
            b'\x13': cls.turn_off,
            b'\x20': cls.switch_color
        }
        function = commands.get(command.type, None)
        if function is None:
            cls.log.error('Unknown function type')
            return
        try:
            function(command.value)
        except LampError as error:
            cls.log.error(error)

    @classmethod
    def turn_on(cls, value):
        '''Включить фонарь.

        :param bytes value: параметр выполнения команды (не используется).

        '''
        if value is not None:
            raise LampError('Command turn_on does not accept value')
        cls.log.info('Lamp turned on')

    @classmethod
    def turn_off(cls, value):
        '''Выключить фонарь.

        :param bytes value: параметр выполнения команды (не используется).

        '''
        if value is not None:
            raise LampError('Command turn_off does not accept value')
        cls.log.info('Lamp turned off')

    @classmethod
    def switch_color(cls, value):
        '''Изменить цвет фонаря.

        :param bytes value: значения цвета фонаря в RGB.

        '''
        if value is None:
            raise LampError('No color value submitted')
        # Значение цвета должно составлять 3 байта
        if len(value) != 3 or not isinstance(value, bytes):
            raise LampError('Incorrect color value')
        rgb = struct.unpack('!BBB', value)
        cls.log.info('Lamp switched color to R:{} G:{} B:{}'.format(*rgb))


class TLVServer(TCPServer):
    '''Сервер управления получающий сообщения формата TLV.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #: Активные в данный момент подключения (IOStream).
        self._streams = set()
        #: Функция выполняемая при получении TLV сообщения.
        self.request_callback = lambda command: None
        self.log = logging.getLogger('tornado.app.server')

    def set_request_callback(self, func):
        '''Установить функцию выполняемую при получении TLV запроса.

        :param func: Функция исполняемая при получении TLV запроса.

        '''
        self.request_callback = func

    @gen.coroutine
    def handle_stream(self, stream, address):
        '''Обработать подключение к серверу.'''
        ip, fileno = address
        self.log.debug('Incoming connection from {}'.format(ip))
        self._streams.add(stream)
        while True:
            try:
                header = yield stream.read_bytes(3)
                mtype, length = struct.unpack('!cH', header)
                if length == 0:
                    value = None
                else:
                    value = yield stream.read_bytes(length)
                self.request_callback(TLVCommand(mtype, value))
            except StreamClosedError:
                self._streams.remove(stream)
                message = 'Client ip:{} fd:{} disconnected.'.format(ip, fileno)
                self.log.debug(message)
                break

    def close_all_connections(self):
        '''Закрыть все активные подключения.'''
        self.log.debug('Closing all active connections')
        while self._streams:
            stream = next(iter(self._streams))
            stream.close()
            self._streams.remove(stream)
        self.log.debug('All active connections closed')


def create_server(address='127.0.0.1', port=9999, loglevel=logging.INFO):
    '''Создать экземпляр сервера для запуска.

    :param str address: Адрес на котором запускается сервер.
    :param int port: Порт на котором запускается сервер.

    :raises: AssertionError, socket.gaioerror
    '''
    assert 0 < port <= 65535, 'Port must be in range 1-65535'
    server = TLVServer()
    log = logging.getLogger('tornado')
    handler = logging.StreamHandler(sys.stdout)
    datefmt = '%Y-%m-%dT%H:%M:%S%z'
    fmt = "%(asctime)s - %(levelname)s - %(message)s"
    handler.setFormatter(LogFormatter(color=False, fmt=fmt, datefmt=datefmt))
    log.addHandler(handler)
    log.setLevel(loglevel)
    server.set_request_callback(LampHandler.dispatch)
    server.bind(port, address)
    server.log.info('Initializing server at {}:{}'.format(address, port))
    return server
