"""Handle receiving and sending of transactions.

Parse the transactions:
    The first byte is the opcode, which is 0.
    The SENDER is the ID of the sender. This is the byte array of their ID
    The RECEIVER is the ID of the receiver. This is the byte array of their ID
"""

import hashlib


class Transaction(object):
    """Handle blockchain transactions."""

    def __init__(self, message_data):
        """Initialize transactions."""
        self.msg_bytearray = message_data  # Original byte array
        transaction_data = self.parse_transaction(message_data)
        (self.sender, self.receiver, self.amount,
         self.timestamp) = transaction_data

    def convert_tx_data(self, hex_input):
        """Convert amount and timestamp attributes to integers."""
        num = ""
        for i in range(len(hex_input) // 2):
            num += chr(int(hex_input[2*i:(2*i)+2], 16))
        return (int(num))

    def compute_transaction_hash(self):
        """Compute hash of current block."""
        # Obtain attributes of transaction class to sum hash values
        sender_bytes = bytes(self.sender, "ascii")
        receiver_bytes = bytes(self.receiver, "ascii")
        amount_bytes = bytes(self.amount, "ascii")
        timestamp_bytes = bytes(self.timestamp, "ascii")
        computed_sum_bytes = (sender_bytes + receiver_bytes + amount_bytes
                              + timestamp_bytes)
        computed_hash = hashlib.sha256(computed_sum_bytes).hexdigest()
        return (computed_hash)

    def parse_transaction(self, byte_message):
        """Parse the byte array of transactions."""
        hex_message = byte_message.hex()
        sender = hex_message[0:64]
        receiver = hex_message[64:128]
        amount = self.convert_tx_data(hex_message[128:192])
        timestamp = self.convert_tx_data(hex_message[192:256])
        # amount = int(hex_message[128:192], 16)
        # timestamp = int(hex_message[192:256], 16)

        return (sender, receiver, amount, timestamp)

    def __str__(self):
        """Pretty printing of transaction for debugging purposes."""
        # DELETE THIS DELETE DELETE DELETE
        return ("\nSender: {} -- Receiver: {} -- Amount: {} -- Timestamp: {}\n".format(
            self.sender, self.receiver, self.amount, self.timestamp))
