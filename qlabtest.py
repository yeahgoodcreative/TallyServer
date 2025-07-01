from enum import Enum

from pythonosc.udp_client import SimpleUDPClient


if __name__ == '__main__':
    client = SimpleUDPClient('127.0.0.1', 53000)
    client.send_message('/cue/test/go', None)
