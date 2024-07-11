import hashlib
import json
from time import time

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, validators):
        self.index = index
        self.timestamp = timestamp
        self.transactions =  [tx.to_dict() for tx in transactions]
        self.previous_hash = previous_hash
        self.validators = validators if validators else {}
        self.hash = self.hash_block() 

    def string(self):
        return f'{self.index}{self.timestamp}{len(self.transactions)}{self.previous_hash}'    

    def hash_block(self):
        def convert_to_serializable(obj):
            if isinstance(obj, bytes):
                return obj.hex()
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(i) for i in obj]
            else:
                return obj

        block_dict = convert_to_serializable(self.__dict__)
        block_string = json.dumps(block_dict, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, -1, [], "0", "Genesis")
        self.chain.append(genesis_block)

    def get_last_block(self):
        return self.chain[-1]  
    


    
    def is_block_in_chain(self, block):
        # Check if the block is already in the blockchain by comparing hashes
        for existing_block in self.chain:
            if existing_block.hash == block.hash:
                return True
        return False

    def add_block(self, block):
        last_block = self.get_last_block()
        if last_block.hash != block.previous_hash:
            return False
        block.hash = block.hash_block()
        self.chain.append(block)
        return True 
    
    def print_blocks(self):
        for block in self.chain:
            print(block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            if current_block.hash != current_block.hash_block():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True