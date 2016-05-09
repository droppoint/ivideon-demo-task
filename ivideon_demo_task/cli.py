import signal

import click
import tornado
from click.exceptions import ClickException

from ivideon_demo_task.server import create_server


@click.group()
@click.help_option(
    help='Отобразить эту справочную информацию и завершить работу'
)
def main(**kwargs):
    '''Тестовое задание для компании Ivideon.'''
    pass


@main.command()
@click.option('-h', '--host', default='localhost', help="Интерфейс сервера")
@click.option('-p', '--port', default=9999, help="Порт сервера")
@click.option("--loglevel", type=click.Choice(('CRITICAL', 'ERROR', 'WARNING',
                                              'INFO', 'DEBUG')),
              default="INFO", help="Уровень выводимых лог сообщений")
def runserver(**kwargs):
    '''Запустить сервер управления фонаря.'''
    try:
        server_kwargs = {
            'address': kwargs['host'],
            'port': kwargs['port'],
            'loglevel': kwargs['loglevel']
        }
        server = create_server(**server_kwargs)
    except (AssertionError, OSError) as error:
        message = 'Ошибка инициализации сервера: {}'.format(str(error))
        raise ClickException(message)

    def shutdown(sig, frame):
        '''callback для штатного завершения работы сервера.'''
        server.log.info('Shutting down server')
        server.close_all_connections()
        server.stop()
        tornado.ioloop.IOLoop.current().stop()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    server.start(1)
    tornado.ioloop.IOLoop.instance().start()
