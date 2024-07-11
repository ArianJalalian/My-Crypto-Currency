from ecdsa import SigningKey, NIST384p

from transaction import Transaction

class Client:
    def __init__(self):
        self.private_key = SigningKey.generate(curve=NIST384p)
        self.public_key = self.private_key.get_verifying_key()

    def get_address(self):
        return self.public_key.to_string().hex()

    def sign_transaction(self, transaction):
        message = f"{transaction['sender']}{transaction['recipient']}{transaction['amount']}".encode()
        return self.private_key.sign(message).hex()

    def create_transaction(self, recipient, amount):
        transaction = {
            'sender': self.get_address(),
            'recipient': recipient,
            'amount': amount
        }
        transaction['signature'] = self.sign_transaction(transaction)
        return Transaction(transaction['sender'], transaction['recipient'], transaction['amount'], transaction['signature'])