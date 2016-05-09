from unittest import mock

from click.testing import CliRunner

from ivideon_demo_task.cli import main


class TestCLI:
    """Интерфейс командной строки"""

    def test_help(self):
        """команда c аргументом --help выводит справку и завершается."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help", ])
        assert result.exit_code == 0
        assert "Тестовое задание для компании Ivideon." in result.output

    @mock.patch("ivideon_demo_task.cli.create_server")
    @mock.patch("ivideon_demo_task.cli.tornado.ioloop.IOLoop")
    def test_run(self, loop_mock, server_mock):
        """runserver запускает сервер в бесконечном цикле."""
        runner = CliRunner()
        args = ['runserver', "-p", "80", "-h", "127.0.0.1"]
        result = runner.invoke(main, args)
        args, kwargs = server_mock.call_args
        expected = {
            'port': 80,
            'loglevel': 'INFO',
            'address': '127.0.0.1'
        }
        assert kwargs == expected
        assert server_mock.return_value.start.called
        assert loop_mock.instance.return_value.start.called
        # Так как вместо запуска loop'а применяется заглушка, команда должна
        # успешно завершиться.
        assert result.exit_code == 0
