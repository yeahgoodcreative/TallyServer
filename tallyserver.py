import os, sys
import configparser
from datetime import datetime

from enum import Enum
from multiprocessing.dummy import Array

from pythonosc.udp_client import SimpleUDPClient
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

from pythonosc.osc_bundle_builder import OscBundleBuilder
from pythonosc.osc_bundle_builder import IMMEDIATELY as OscBundleBuilderIMMEDIATELY

from pythonosc.osc_message_builder import OscMessageBuilder


if __name__ == '__main__':
    print("TallyServer V1.1.0")
    print("Developed by Yeah Good Creative (www.yeahgoodcreative.com.au)")
    print()

    config = configparser.ConfigParser()

    EXE_DIR = os.path.dirname(sys.executable)
    CONFIG_PATH = os.path.abspath(EXE_DIR + '/config.ini')
    
    print('Loading config from ' + CONFIG_PATH)
    res = config.read(CONFIG_PATH)

    if (res == []):
        print('ERROR: Config file not found')
        while True: 
            None

    print('Reading parameters from config file...')
    print()

    tallyServerAddress      = config['DEFAULT']['TallyServerAddress']
    tallyServerPort         = int(config['DEFAULT']['TallyServerPort'])
    print('\tTally Server Address: \t' + tallyServerAddress)
    print('\tTally Server Port: \t' + str(tallyServerPort))
    print()

    qlabAddress             = config['DEFAULT']['QlabAddress']
    qlabPort                = int(config['DEFAULT']['QlabPort'])
    print('\tQLab Address: \t\t' + qlabAddress)
    print('\tQLab Port: \t\t' + str(qlabPort))
    print()

    remotesAddress          = config['DEFAULT']['RemotesAddress']
    remotesPort             = int(config['DEFAULT']['RemotesPort'])
    print('\tRemotes Address: \t' + remotesAddress)
    print('\tRemotes Port: \t\t' + str(remotesPort))
    print()

    participants            = int(config['DEFAULT']['Participants'])
    print('\tParticipants: \t\t' + str(participants))
    print()

    class State(Enum):
        STARTED     = 0
        STOPPED     = 1

    STATE           = State.STOPPED

    # participants = 25
    votes = [0] * participants

    votes1 = 0
    votes2 = 0
    votes3 = 0
    votesT = 0

    def countVotes():
        global votes1; global votes2; global votes3; global votesT
        
        votes1 = 0
        votes2 = 0
        votes3 = 0

        for x in votes:
            match x:
                case 1:
                    votes1 += 1

                case 2:
                    votes2 += 1

                case 3:
                    votes3 += 1

        votesT = votes1 + votes2 + votes3



    qlab_client = SimpleUDPClient(qlabAddress, qlabPort, True)
    remote_client = SimpleUDPClient(remotesAddress, remotesPort, True)

    def tally():
        global votes1; global votes2; global votes3; global votesT

        print(str(datetime.now()) + '\t\t' + 'TALLY G: ' + str(votes1) + ' B: ' + str(votes2) + ' R: ' + str(votes3) + ' TOTAL: ' + str(votesT))
        qlab_client.send_message('/cue/g' + str(votes1) + '/start', None)
        qlab_client.send_message('/cue/b' + str(votes2) + '/start', None)
        qlab_client.send_message('/cue/r' + str(votes3) + '/start', None)
        qlab_client.send_message('/cue/total' + str(votesT) + '/start', None)

    def currentWinner():
        global votes1; global votes2; global votes3; global votesT

        # Votes 1 Winning
        if (votes1 > votes2 and votes1 > votes3):
            qlab_client.send_message('/cue/gwin/start', None)
    
        # Votes 2 Winning
        if (votes2 > votes1 and votes2 > votes3):
            qlab_client.send_message('/cue/bwin/start', None)

        # Votes 3 Winning
        if (votes3 > votes1 and votes3 > votes2):
            qlab_client.send_message('/cue/rwin/start', None)
            

        # Votes 1 & 2 Tie
        if (votes1 == votes2 and votes1 > votes3 and votes2 > votes3):
            qlab_client.send_message('/cue/bgtie/start', None)

        # Votes 1 & 3 Tie
        if (votes1 == votes2 and votes1 > votes3 and votes2 > votes3):
            qlab_client.send_message('/cue/rgtie/start', None)

        # Votes 2 & 3 Tie
        if (votes2 == votes3 and votes2 > votes1 and votes3 > votes1):
            qlab_client.send_message('/cue/rbtie/start', None)

        # Votes 1, 2 & 3 Tie
        if (votes1 == votes2 and votes2 == votes3):
            qlab_client.send_message('/cue/rbgtie/start', None)
        
    
    

    def qlab_handler(address, *args):
        global STATE
        global votes; votes1; global votes2; global votes3; global votesT

        match address:
            case '/tally/reset':
                votes = [0] * participants
                countVotes()
                print(str(datetime.now()) + '\t\t' + 'TALLY RESET')
                print(str(datetime.now()) + '\t\t' + 'TALLY G: ' + str(votes1) + ' B: ' + str(votes2) + ' R: ' + str(votes3) + ' TOTAL: ' + str(votesT))


            case '/tally/start':
                if (STATE == State.STOPPED):
                    STATE = State.STARTED
                    remote_client.send_message('/remotes/leds', [255, 255, 255])
                    print(str(datetime.now()) + '\t\t' + 'TALLY START')


            case '/tally/stop':
                if (STATE == State.STARTED):
                    STATE = State.STOPPED
                    print(str(datetime.now()) + '\t\t' + 'TALLY STOP')
                remote_client.send_message('/remotes/leds', [0, 0, 0])
                


    def remote_handler(address, *args):
        splitAddress = address.split('/')
        splitAddress.pop(0); splitAddress.pop(0)

        match splitAddress[1]:
            case 'button':
                if (STATE == State.STOPPED):
                    return

                remote = splitAddress[0]
                button = splitAddress[2]

                print(str(datetime.now()) + '\t\t' + 'RECEIVED Remote ' + str(remote) + ' Button ' + str(button))

                match button:
                    case '1':
                        votes[int(remote)-1] = 1
                        remote_client.send_message('/remote/' + remote + '/leds', [255, 0, 0])
                        qlab_client.send_message('/cue/' + remote + 'g/start', None)

                        countVotes()
                        tally()
                        currentWinner()

                    case '2':
                        votes[int(remote)-1] = 2
                        remote_client.send_message('/remote/' + remote + '/leds', [0, 255, 0])
                        qlab_client.send_message('/cue/' + remote + 'b/start', None)

                        countVotes()
                        tally()
                        currentWinner()

                    case '3':
                        votes[int(remote)-1] = 3
                        remote_client.send_message('/remote/' + remote + '/leds', [0, 0, 255])
                        qlab_client.send_message('/cue/' + remote + 'r/start', None)

                        countVotes()
                        tally()
                        currentWinner()


    def reset():
        global votes1; global votes2; global votes3; global votesT
        print('BEFORE RESET - R: ' + str(votes1) + ' B: ' + str(votes2) + ' G: ' + str(votes3) + ' TOTAL: ' + str(votesT))

        votes1 = 0
        votes2 = 0
        votes3 = 0
        votesT = 0
        print('AFTER RESET - R: ' + str(votes1) + ' B: ' + str(votes2) + ' G: ' + str(votes3) + ' TOTAL: ' + str(votesT))

    # reset()
    # countVotes()
    # tally()
    # currentWinner()

    # votes1 += 2
    # votes2 += 1
    # votes3 += 1

    # reset()
    # countVotes()
    # tally()
    # currentWinner()



    dispatcher = Dispatcher()
    dispatcher.map('/tally/*', qlab_handler)
    dispatcher.map('/tally/*/button/*', remote_handler)

    server = BlockingOSCUDPServer((tallyServerAddress, tallyServerPort), dispatcher)

    print('Starting server...')
    server.serve_forever()  # Blocks forever