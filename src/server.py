"""Initiate a server to receive transactions from other nodes.

Tasks:
    When node accepts connection, read in message from sender
    Handle how much money senders and receivers have in their accounts
    Broadcast transactions to peers
"""

import time
import socket
import argparse
import multiprocessing as mp

from transaction import Transaction
from block import Block
from utxo import UTXO

# Opcode variables to create mapping between message size
TX_OPCODE = "0"
CLOSE_OPCODE = "1"
BLOCK_OPCODE = "2"
GET_BLOCK_OPCODE = "3"


class Server(object):
    """Initialize sockets to receive and transmit blockchain data."""

    def __init__(self):
        """Initialize the server to handle information."""
        parser_arguments = self.parse_commandline()
        (self.port, self.peers, self.difficulty,
         self.numtxinblock, self.numcores) = parser_arguments
        self.utxo = UTXO(self.numtxinblock, self.difficulty, self.numcores)
        self.message_map = self.message_mapping()  # Opcodes and message sizes
        self.socket = self.create_socket()
        self.close_status = mp.Value('i', 0)  # Checks close status
        self.socket_list = []  # Hold sockets for peers
        self.broadcasting = True
        self.listen_socket()  # Listen for clients
        # self.create_peer_sockets()  # Connect peer sockets for broadcasting

    def parse_commandline(self):
        """Handle command line arguments."""
        arg_parser = argparse.ArgumentParser()
        arg_parser.add_argument('--port', help="Port node is listening on",
                                required=True)
        arg_parser.add_argument('--peers', help="Comma separated list of peer ports",
                                required=True)
        arg_parser.add_argument('--difficulty', help="Number of leading bytes",
                                default=0, required=False)
        arg_parser.add_argument('--numtxinblock', default=50000,
                                help="Transactions in a block", required=False)
        arg_parser.add_argument('--numcores', default=0,
                                help="Number of cores", required=False)

        # List of arguments
        print("Parsing arguments.")
        arg_list = arg_parser.parse_args()
        port = int(arg_list.port)
        peers = arg_list.peers.split(',')
        difficulty = int(arg_list.difficulty)
        numtxinblock = int(arg_list.numtxinblock)
        numcores = int(arg_list.numcores)

        return (port, peers, difficulty, numtxinblock, numcores)

    def message_mapping(self):
        """Opcodes for message types and respective size mapping."""
        message_size = {TX_OPCODE: 128, CLOSE_OPCODE: 0,
                        BLOCK_OPCODE: (160 + (128*self.numtxinblock)),
                        GET_BLOCK_OPCODE: 32}
        return (message_size)

    def create_socket(self):
        """Initialize socket for node to begin receiving requests."""
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        new_socket.bind(('localhost', self.port))
        return (new_socket)

    def listen_socket(self):
        """Listen for new clients individually."""
        self.socket.listen(10)
        print("Socket is listening on port: ", self.port)
        process_queue = []  # Create queue to hold processes
        while True:
            if(self.close_status.value == 0):
                client, address = self.socket.accept()
                print("Connection received from: ", address)
                cur_process = mp.Process(target=self.connect_socket,
                                         args=(client, address))
                process_queue.append(cur_process)  # Hold processes
                cur_process.start()
            else:
                print("Received close message.")
                break   # If close has been called, stop listening
            for p in process_queue:
                p.join()

    def create_peer_sockets(self):
        """Create sockets for each peer node."""
        for peer in self.peers:  # Broadcast to all peers in list
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("Connecting to peer: ", peer)
            peer_socket.connect(('localhost', int(peer)))
            self.socket_list.append(peer_socket)  # Add socket to list
        print("Peer socket list: ", self.socket_list)

    def broadcast_message(self, message):
        """Share transactions/blocks with peer nodes."""
        for peer_socket in self.socket_list:  # Broadcast to all peers in list
            print ("Broadcasting to peer socket.")
            peer_socket.send(message)
            print ("Broadcasting to peer finished.")

    def close_peer_sockets(self):
        """Close list of peer sockets."""
        for peer_socket in self.socket_list:
            peer_socket.close()

    def process_data_bytes(self, client_socket):
        """Only receive bytes of a certain message."""
        # Receive first byte, check it then receive more
        # If this is done, no need to truncate data
        receiving_data = client_socket.recv(1)
        message = bytearray()
        message.extend(receiving_data)
        if (len(message) > 0):
            opcode = chr(int(message[0:1].hex(), 16))  # Check opcode of byte
            message.extend(client_socket.recv(self.message_map.get(opcode)))
            # print("Error!")
        return (message)

    def connect_socket(self, client_socket, client_address):
        """Handle connections and incoming data."""
        start_time = time.time()  # Start recording time
        self.create_peer_sockets()  # Connect peer sockets for broadcasting
        message = self.process_data_bytes(client_socket)
        while message:
            print("Length of current message is:", len(message))
            opcode = chr(int(message[0:1].hex(), 16))  # Get opcode
            print ("Current opcode: ", opcode)

            # Get specific message
            msg_start = 1
            msg_end = 1 + self.message_map.get(opcode)
            current_message = message[msg_start: msg_end]
            msg_with_opcode = message[0: msg_end]

            # Based on current opcode, execute specific action
            if opcode == TX_OPCODE:
                # Create transaction and broadcast if legal
                new_tx = Transaction(current_message)
                broadcasting, block = self.utxo.process_transaction(new_tx)
            elif opcode == CLOSE_OPCODE:
                self.close_status.value = 1  # Indicate close
                broadcasting = True  # Forward close signal to peers
                block = False
                print("Broadcasting close message.")
                # self.stop()
            elif opcode == BLOCK_OPCODE:
                broadcasting = False
                # Initialize received block
                block = Block(self.difficulty, msg_with_opcode, self.numcores)
                print("Block received: ", block)
            elif opcode == GET_BLOCK_OPCODE:
                # Pass specified block information to sender
                block_at_height = self.utxo.process_get_block(current_message)
                client_socket.send(block_at_height)

            # Decide when to broadcast transactions and blocks
            if broadcasting and block:
                self.broadcast_message(msg_with_opcode)
                self.broadcast_message(block.msg_bytearray)
                print ("Block and transaction broadcast to peer.")
            elif block:
                self.broadcast_message(block.msg_bytearray)
                print ("Block broadcast to peer.")
            elif broadcasting:
                self.broadcast_message(msg_with_opcode)

            # Read in more data
            message = self.process_data_bytes(client_socket)

        # Message is completely read and node will close down
        self.close_peer_sockets()  # Close peers after finishing
        self.close()
        end_time = time.time()  # Stop recording time
        work_time = end_time - start_time  # Compute duration of process
        print ("Time to run blockchain: ", work_time)

    def close(self):
        """Close the node socket."""
        self.socket.close()
