from blockchain import Blockchain, Block
from transaction import Transaction


import json

from ecdsa import SigningKey, NIST384p
from ecdsa import VerifyingKey, NIST384p
from time import time


class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.blockchain = Blockchain()
        self.mempool = [] 
        self.neighbors = []
        self.balances = {}
        self.authority_public_keys = {}
        self.authority_nodes = [] 


    def add_authority_node(self, authority_node, authority_public_key):
        self.authority_nodes.append(authority_node)
        self.authority_public_keys[authority_node.node_id] = authority_public_key

    def add_transaction(self, transaction): 
        if self.validate_transaction(transaction): 
            self.mempool.append(transaction)
            self.broadcast_transaction(transaction)
            return self.blockchain.get_last_block().index + 1
        return False

    def broadcast_transaction(self, transaction):
        for authority in self.authority_nodes:
            authority.receive_transaction(transaction)

    def receive_transaction(self, transaction):
        if self.validate_transaction(transaction) and not transaction in self.mempool:
            self.mempool.append(transaction)
            return True
        return False 
    
    def broadcast_block(self, block):
            for neighbor in self.neighbors:
                neighbor.receive_block(block) 

    def validate_transaction(self, transaction):        
        # Validate signature
        message = f"{transaction.sender}{transaction.recipient}{transaction.amount}".encode()
        signature = bytes.fromhex(transaction.signature)
        verifying_key = VerifyingKey.from_string(bytes.fromhex(transaction.sender), curve=NIST384p)
        try:
            if not verifying_key.verify(signature, message):
                return False
        except:
            return False 
        
        # Validate transaction hash
        if transaction.hash != transaction.hash_transaction():
            return False 
        
        # Validate balance
        sender_balance = self.balances[transaction.sender]
        if sender_balance < transaction.amount:
            return False

        return True

    def is_validated(self, block):
        # Dictionary to count valid signatures for each authority
        signature_counts = {}

        # Check each validator's signature in the block
        for validator, signature in block.validators.items():
            if validator in self.authority_public_keys: 
                # Verify the signature using the authority node's public key
                public_key = self.authority_public_keys[validator] 

                string = block.string().encode()
                signature = bytes.fromhex(signature)
                verifying_key = VerifyingKey.from_string(bytes.fromhex(public_key), curve=NIST384p)
                try:
                    if not verifying_key.verify(signature, string): 
                        signature_counts[validator] = False 
                    else:
                        signature_counts[validator] = True
                except: 
                    signature_counts[validator] = False 
                # try:
                #     public_key.verify(
                #         bytes.fromhex(signature),
                #         json.dumps(block.__dict__, sort_keys=True).encode(),
                #         padding.PSS(
                #             mgf=padding.MGF1(hashes.SHA256()),
                #             salt_length=padding.PSS.MAX_LENGTH
                #         ),
                #         hashes.SHA256()
                #     )
                # except Exception as e:
                #     signature_counts[validator] = False 
    

        # Calculate the number of valid signatures
        num_valid_signatures = sum(signature_counts.values())

        # Calculate the threshold (50% of the total number of authorities)
        num_authorities = len(self.authority_public_keys)
        threshold = num_authorities / 2

        # Check if the block is validated (at least 50% of authorities signed)

        return num_valid_signatures >= threshold

    def receive_block(self, block):
        # Check if block is already in chain 
        if self.blockchain.is_block_in_chain(block): 
            return False

        # Validate block and its transactions
        if self.is_validated(block):
            # Add block to own blockchain
            self.blockchain.add_block(block)
            self.mempool = [tx for tx in self.mempool if tx.to_dict() not in block.transactions] 
            self.update_balances(block.transactions)

            # Broadcast the block to neighbors
            self.broadcast_block(block)

            return True

        return False

    def update_balances(self, transactions):
        for tx in transactions:
            self.balances[tx['sender']] -= tx['amount']
            self.balances[tx['recipient']] = self.balances.get(tx['recipient'], 0) + tx['amount']

class AuthorityNode(Node):
    def __init__(self, node_id, authority_private_key):
        super().__init__(node_id)
        self.authority_private_key = authority_private_key 

    def create_new_block(self): 
        if len(self.mempool) == 0: 
            return None 
        previous_block = self.blockchain.get_last_block()
        new_block = Block(len(self.blockchain.chain), time(), self.mempool, previous_block.hash, None)
        new_block.hash = new_block.hash_block() 
        if not self.validate_block(new_block): 
            return None
        self.blockchain.add_block(new_block)
        self.mempool = []
        self.update_balances(new_block.transactions) 
        self.first_broadcast_block(new_block)
        return new_block     
    
    def first_broadcast_block(self, block):
        for node in self.authority_nodes:
           if node.receive_block(block):  
                if self.authority_public_keys[self.node_id] not in self.balances:
                    self.balances[self.authority_public_keys[self.node_id]] = 0    
                self.balances[self.authority_public_keys[self.node_id]] += 1  

        self.broadcast_block(block)        

    def validate_block(self, block):
        # Create a copy of the current balances for simulation
        simulated_balances = self.balances.copy()

        # Check each transaction in the block
        for tx_dict in block.transactions:
            tx = Transaction(
                tx_dict['sender'],
                tx_dict['recipient'],
                tx_dict['amount'],
                tx_dict['signature']
            )

            # Check if transaction is valid
            if not self.validate_transaction(tx):
                return False

            # Simulate the transaction
            sender_balance = simulated_balances.get(tx.sender, 0)
            recipient_balance = simulated_balances.get(tx.recipient, 0)

            # Check if the sender has enough balance
            if sender_balance < tx.amount:
                return False

            # Update the simulated balances
            simulated_balances[tx.sender] -= tx.amount
            simulated_balances[tx.recipient] = recipient_balance + tx.amount

        # If all transactions are valid and no balance goes negative, sign the block
        block_signature = self.sign_block(block)
        block.validators[self.node_id] = block_signature

        return True
    
    def sign_block(self, block):
        string = block.string().encode()
        return self.authority_private_key.sign(string).hex()

    def receive_block(self, block):
        # Check if block is already in chain
        if self.blockchain.is_block_in_chain(block):
            return False

        # Validate block and its transactions
        if self.validate_block(block):  
            print()
            # Add block to own blockchain
            self.blockchain.add_block(block)
            self.mempool = [tx for tx in self.mempool if tx.to_dict() not in  block.transactions]
            self.update_balances(block.transactions)

            # Broadcast the block to neighbors
            self.broadcast_block(block)

            return True

        return False