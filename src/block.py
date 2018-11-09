"""Maintain how much money each sender and receiver has in their account.

Tasks:
    When node receives transaction, look up sender and receiver
    Add/remove corresponding transaction amount
    Broadcast all transactions to peers
"""

import hashlib
import multiprocessing as mp


class Block(object):
    """Handle blockchain transactions."""

    def __init__(self, difficulty, message_data, numcores):
        """Initialize the UTXO set to handle ledger."""
        self.difficulty = difficulty
        self.msg_bytearray = message_data  # Original byte array
        self.numcores = numcores
        self.nonce_status = mp.Value('i', 0)  # Checks nonce status
        block_objects = self.parse_block(message_data)
        (self.nonce, self.prior_hash, self.hash, self.block_height,
         self.miner_address, self.block_data) = block_objects

    def convert_block(self, ascii_input):
        """Convert specific block attributes to integers."""
        num = ""
        for i in range(len(ascii_input) // 2):
            num += chr(int(ascii_input[2*i:(2*i)+2], 16))
        return (int(num))

    def compute_block_hash(self):
        """Compute hash of current block."""
        # Obtain attributes of block class to sum hash values
        nonce_bytes = bytes(str(self.nonce), "ascii")
        prior_hash_bytes = bytes(str(self.prior_hash), "ascii")
        block_height_bytes = bytes(str(self.block_height), "ascii")
        miner_address_bytes = bytes(str(self.miner_address), "ascii")
        block_data_bytes = bytes(str(self.block_data), "ascii")
        computed_sum = (nonce_bytes + prior_hash_bytes + block_height_bytes
                        + miner_address_bytes + block_data_bytes)
        computed_hash = hashlib.sha256(computed_sum).hexdigest()
        # Update bytearray with new nonce value
        computed_hashbytes = bytes.fromhex(computed_hash)
        self.msg_bytearray = (self.msg_bytearray[0:96] + computed_hashbytes
                              + self.msg_bytearray[128:])
        return (computed_hash)

    def parse_block(self, byte_message):
        """Parse the byte array of transactions."""
        hex_message = byte_message.hex()
        # nonce = int(hex_message[0:64], 16)
        nonce = self.convert_block(hex_message[0:64])
        prior_hash = hex_message[64:128]
        present_hash = hex_message[128:192]
        # block_height = self.convert_block(hex_message[192:256])
        # miner_address = self.convert_block(hex_message[256:320])
        # block_data = self.convert_block(hex_message[320:])
        block_height = int(hex_message[192:256], 16)
        miner_address = int(hex_message[256:320], 16)
        block_data = int(hex_message[320:], 16)

        return (nonce, prior_hash, present_hash, block_height,
                miner_address, block_data)

    def mine_block(self):
        """Mine block once node has a certain number of transactions."""
        difficulty_zeroes = self.difficulty * "0"  # Number of zeroes needed
        # Mine block until an appropriate nonce has been found
        print("Original nonce: ", self.nonce)
        while (self.hash[0:self.difficulty] != difficulty_zeroes):
            self.nonce += 1
            self.hash = self.compute_block_hash()
        print ("Block mined.")

    def cores_mine_block(self, core_number):
        """Mine block once node has a certain number of transactions."""
        difficulty_zeroes = self.difficulty * "0"  # Number of zeroes needed
        print("Difficulty zeros: ", difficulty_zeroes)
        # Mine block until an appropriate nonce has been found
        print("Original nonce: ", self.nonce)
        print ("Current core: ", core_number)
        nonce = self.nonce
        print("Copy of nonce", nonce)
        while (self.hash[0:self.difficulty] != difficulty_zeroes):
            nonce += core_number
            self.hash = self.compute_block_hash()
        self.nonce_status.value = 1  # Nonce has been found
        print ("Block mined and nonce found: ", nonce)
        self.nonce = nonce

    def mine_blocks(self):
        """Use multiprocessing to enhance block mining."""
        nonce_processes = []
        core_range = range(1, self.numcores + 1)
        while True:
            if (self.nonce_status.value == 0):
                for core in core_range:
                    core_proc = mp.Process(target=self.cores_mine_block,
                                           args=(core,))
                    nonce_processes.append(core_proc)
                    core_proc.start()
            else:
                break
            for process in nonce_processes:  # Terminate processes
                process.join()
                # process.terminate()

    def __str__(self):
        """Pretty printing of block for debugging purposes."""
        return ("\n Nonce: {} -- Prior Hash: {} -- Hash: {} -- Blockheight: {} -- Miner Address: {} -- Blockdata: {}\n".format(
            self.nonce, self.prior_hash, self.hash, self.block_height,
            self.miner_address, self.block_data))
