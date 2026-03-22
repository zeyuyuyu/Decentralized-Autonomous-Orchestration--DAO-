import hashlib
import time
import json
from typing import List, Tuple

class DecentralizedConsensus:
    def __init__(self, nodes: List[str], difficulty: int = 4):
        self.nodes = nodes
        self.difficulty = difficulty
        self.chain = []
        self.pending_transactions = []
        self.genesis_block()

    def genesis_block(self):
        genesis = {
            'index': 0,
            'timestamp': time.time(),
            'transactions': [],
            'proof': 0,
            'previous_hash': '0'
        }
        self.chain.append(genesis)

    def proof_of_work(self, block: dict) -> int:
        proof = 0
        while self.valid_proof(block, proof) is False:
            proof += 1
        return proof

    def valid_proof(self, block: dict, proof: int) -> bool:
        block_string = json.dumps(block, sort_keys=True).encode()
        guess = hashlib.sha256(block_string).hexdigest()
        return guess[:self.difficulty] == '0' * self.difficulty

    def add_transaction(self, sender: str, recipient: str, amount: float) -> int:
        self.pending_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })
        return len(self.chain) + 1

    def mine_block(self) -> Tuple[dict, int]:
        if not self.pending_transactions:
            return None, None

        last_block = self.chain[-1]
        new_block = {
            'index': len(self.chain),
            'timestamp': time.time(),
            'transactions': self.pending_transactions,
            'proof': self.proof_of_work(last_block),
            'previous_hash': self.hash(last_block)
        }

        self.pending_transactions = []
        self.chain.append(new_block)
        return new_block, len(self.chain)

    @staticmethod
    def hash(block: dict) -> str:
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def valid_chain(self, chain: List[dict]) -> bool:
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            if block['previous_hash'] != self.hash(last_block):
                return False

            if not self.valid_proof(last_block, block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self) -> bool:
        neighbors = self.nodes
        longest_chain = self.chain

        for node in neighbors:
            response = node.get_chain()
            if len(response['chain']) > len(longest_chain):
                if self.valid_chain(response['chain']):
                    longest_chain = response['chain']
                    self.chain = longest_chain
                    return True

        return False
