from unittest import mock

import pytest

from ivideon_demo_task.server import (
    create_server, LampError, LampHandler, TLVCommand, TLVServer)


class TestLampHandler:
    '''LampHandler'''

    @pytest.mark.parametrize("ctype, value, function", [
        (b'\x12', None, 'turn_on'),
        (b'\x13', None, 'turn_off'),
        (b'\x20', b'\x20\x21\x22', 'switch_color')
    ])
    def test_dispatch(self, ctype, value, function):
        '''dispatch вызывает соответствующий команде метод управления.'''
        command = TLVCommand(ctype, value)
        path = 'ivideon_demo_task.server.LampHandler.{}'.format(function)
        with mock.patch(path) as func_mock:
            func_mock.return_value = None
            LampHandler.dispatch(command)
            assert func_mock.call_count == 1

    def test_dispatch_unknown(self, caplog):
        '''dispatch заносит сообщение в лог, если была получена команда
        управления неизвестного типа.
        '''
        command = TLVCommand(b'\x00', None)
        LampHandler.dispatch(command)
        assert "Unknown function type" in caplog.text()

    @mock.patch('ivideon_demo_task.server.LampHandler.switch_color')
    def test_dispatch_error(self, func_mock, caplog):
        '''dispatch заносит сообщение в лог, если при выполнении команды
        управления возникла ошибка.
        '''
        func_mock.side_effect = LampError('Test abcdef')
        command = TLVCommand(b'\x20', b'\x20\x21\x22')
        LampHandler.dispatch(command)
        assert 'Test abcdef' in caplog.text()

    @pytest.mark.parametrize("ctype, value, message", [
        (b'\x12', None, 'Lamp turned on'),
        (b'\x12', b'\x12', 'Command turn_on does not accept value'),
        (b'\x13', None, 'Lamp turned off'),
        (b'\x13', b'\x13', 'Command turn_off does not accept value'),
        (b'\x20', b'\x20\x21\x22', 'Lamp switched color'),
        (b'\x20', None, 'No color value submitted'),
        (b'\x20', b'\x20\x21', 'Incorrect color value'),
        (b'\x20', '011', 'Incorrect color value'),
    ])
    def test_commands(self, ctype, value, message, caplog):
        '''dispatch корректно обрабатывает команды в том числе и некорректные.
        '''
        command = TLVCommand(ctype, value)
        LampHandler.dispatch(command)
        assert message in caplog.text()


class TestTLVServer:
    '''TLVServer'''

    def test_init(self):
        '''при инициализации не имеет активных соединений, имеет пустой
        обработчик TLV запрос и инициализированный логгер
        '''
        server = TLVServer()
        assert server._streams == set()
        assert callable(server.request_callback)
        assert server.log


class TestCreateServer:
    '''create_server'''

    def test_ok(self):
        '''создает сервер готовый к запуску, если параметры корректны.'''
        server = create_server('127.0.0.1', 9999)
        assert isinstance(server, TLVServer)

    def test_incorrect_port(self):
        '''вызывает AssertionError, если номер порта некорректен.'''
        with pytest.raises(AssertionError) as excinfo:
            create_server('127.0.0.1', 1000000000)
        assert 'Port must be in range 1-65535' in str(excinfo.value)

    def test_incorrect_address(self):
        '''вызывает OSError, если адрес некорректен.'''
        with pytest.raises(OSError) as excinfo:
            create_server('4.4.4.4', 9999)
        assert 'Cannot assign requested address' in str(excinfo.value)

    def test_incorrect_address_already_used(self):
        '''вызывает OSError, если адрес некорректен.'''
        server_a = create_server('127.0.0.1', 9999)
        server_a.start()
        with pytest.raises(OSError) as excinfo:
            create_server('127.0.0.1', 9999)
        server_a.stop()
        assert 'Address already in use' in str(excinfo.value)
