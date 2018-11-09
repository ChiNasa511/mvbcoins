"""Maintain how much money each sender and receiver has in their account.

Tasks:
    When node receives transaction, look up sender and receiver
    Add/remove corresponding transaction amount
    Broadcast all transactions to peers
"""

from hashlib import sha256
from block import Block


class UTXO(object):
    """Handle blockchain transactions."""

    def __init__(self, numtxinblock, difficulty, numcores):
        """Initialize the UTXO set to work as a ledger."""
        self.utxo = self.create_utxo()
        self.numtxinblock = numtxinblock
        self.difficulty = difficulty
        self.numcores = numcores
        self.transaction_list = []  # List of transaction byte array data
        self.block_list = []  # List of block data

    def create_utxo(self):
        """Define and initalize UTXO set."""
        utxo_set = {}
        for i in range(100):
            account = sha256(bytes(str(i), 'ascii')).hexdigest()
            utxo_set[account] = 100000
        return (utxo_set)

    def check_balances(self, transaction):
        """Check for double spending transactions."""
        return (self.utxo[transaction.sender] > transaction.amount)

    def check_double_spending(self, transaction):
        """Check for double spending transactions."""
        return (transaction.msg_bytearray in self.transaction_list)

    def check_sender_receiver(self, transaction):
        """Check for double spending transactions."""
        return (transaction.sender in self.utxo
                and transaction.receiver in self.utxo)

    def store_transaction(self, transaction):
        """Store processed transactions in list."""
        self.transaction_list.append(transaction.msg_bytearray)
        print ("Transaction processed: ", transaction)

    def process_transaction(self, transaction):
        """Maintain transaction history and account balances."""
        sender = transaction.sender
        receiver = transaction.receiver
        amount = transaction.amount

        # Obtain balances
        sender_balance = self.utxo[sender]
        receiver_balance = self.utxo[receiver]

        # Add money to receiver account/remove money from sender account
        new_sendbalance = sender_balance - amount
        new_recvbalance = receiver_balance + amount

        # Check for double spending before processing transaction
        if (not self.check_double_spending(transaction)
                and self.check_sender_receiver(transaction)
                and self.check_balances(transaction)):
            # Update balances if sender has enough money
            # if (sender_balance > amount):
            self.utxo[receiver] = new_sendbalance
            self.utxo[sender] = new_recvbalance
            self.store_transaction(transaction)  # Note transaction
            # Initiate mining process
            if (len(self.transaction_list) == self.numtxinblock):
                mined_block = self.mine()
                self.process_block(mined_block)  # Store block
                return (True, mined_block)  # Broadcast mined block
            return (True, None)  # Ensure transaction gets broadcast
        else:
            print ("Transaction not processed: double spending")
            return (False, None)  # Do not broadcast bad transactions

    def padding(self, input_byte, byte_length):
        """Pad nonce to ensure byte length of 32."""
        pad_amount = byte_length - len(input_byte)
        input_byte += (b'0' * pad_amount)  # Pad to get desired byte length
        return (input_byte)

    def mine(self):
        """Create a new block through mining."""
        # Check whether genesis block needs to be created or not
        if (len(self.block_list) == 0):  # genesis block is already in list
            prior_hash = sha256(bytes("0", 'ascii')).digest()  # Genesis block
        else:
            prior_hash = bytes.fromhex(self.block_list[len(self.block_list) - 1].hash)
        nonce = self.padding(bytes("1", "ascii"), 32)
        block_hash = self.padding(bytes([0]), 32)
        block_height = self.padding(bytes(str(len(self.block_list)),
                                          "ascii"), 32)
        miner_address = self.padding(bytes("cto9", "ascii"), 32)
        block_data = b''.join(self.transaction_list)
        message_data = (nonce + prior_hash + block_hash + block_height
                        + miner_address + block_data)
        new_block = Block(self.difficulty, message_data, self.numcores)
        new_block.mine_blocks()  # Mine block
        self.transaction_list = []  # Empty transaction list
        return (new_block)

    def store_block(self, block):
        """Store processed blocks in list."""
        self.block_list.append(block)

    def process_block(self, block):
        """Maintain block history."""
        self.store_block(block)  # Note block
        print ("Block processed: ", block)
        return (True)  # Ensure that block gets broadcast to peers

    def process_get_block(self, block_height):
        """Retrieve block at specified height."""
        if block_height <= len(self.block_list):
            return (self.block_list[block_height-1])
