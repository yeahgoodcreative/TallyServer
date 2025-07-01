from enum import Enum

from pythonosc.udp_client import SimpleUDPClient
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer


class State(Enum):
    STARTED     = 0
    STOPPED     = 1


STATE           = State.STOPPED
PARTICIPANTS    = 1


if __name__ == '__main__':
    qlab_client = SimpleUDPClient('127.0.0.1', 53000)
    remote_client = SimpleUDPClient('192.168.1.165', 53000)

    def qlab_handler(address, *args):
        splitAddress = address.split('/')
        splitAddress.pop(0); splitAddress.pop(0)

        match splitAddress[0]:
            case 'reset':
                print('RESET')
                remote_client.send_message('/remotes/lock', None)

            case 'start':
                print('START')
                remote_client.send_message('/remotes/unlock', None)

            case 'stop':
                None

            case 'getresult':
                qlab_client.send_message('/qlab/result', None)

            case 'getprogress':
                qlab_client.send_message('/qlab/progress', None)


    def vote_handler(address, *args):
        print(f'{address}: {args}')

    dispatcher = Dispatcher()
    dispatcher.map('/tallyvote/*', qlab_handler)
    dispatcher.map('/remote/*/vote', vote_handler)

    server = BlockingOSCUDPServer(('0.0.0.0', 53001), dispatcher)
    server.serve_forever()  # Blocks forever