import random
import json
import hashlib
import queue
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

# From https://codereview.stackexchange.com/a/260276
def str_bin_in_4digits(hex_string: str) -> str:
    """
    Turn a hex string into a binary string.
    In the output string, binary digits are space separated in groups of 4.
    >>> str_bin_in_4digits('20AC')
    '0010000010101100'
    """

    return f"{int(hex_string,16):0{len(hex_string)*5-1}_b}".replace('_', '')

class Node():
    def __init__(self):
        self.id = random.getrandbits(32)
        self.node_list = [self.id]
        self.vote = random.getrandbits(32)
        self.voter_list = {str(self.id) : self.vote}
        self._is_leader = False
        self._is_solved = False
        self.challenge = 0

        # cryptography
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
        self.public_key = self.private_key.public_key()
        self.node_keys = {str(self.id) : self.public_key}

    # getters and setters
    def get_id(self):
        return self.id
    
    def get_vote(self):
        return self.vote
    
    def get_num_nodes(self):
        return len(self.node_list)
    
    def is_leader(self):
        return self._is_leader

    def is_solved(self):
        return self._is_solved
    
    def set_is_solved(self):
        self._is_solved = True
    
    def get_num_voters(self):
        return len(self.voter_list)
    
    def add_node_init(self, new_id):
        if new_id not in self.node_list:
            self.node_list.append(new_id)
    
    def add_node_voting(self, vote):
        self.voter_list.update({vote['NodeID'] : vote['VoteID']})

    # ops
    def election(self):
        winner = max(self.voter_list, key=self.voter_list.get)
        if int(winner) == self.id:
            self._is_leader = True
            print(f'I\'m the leader!')
        else:
            self._is_leader = False
            print(f'I\'m a node!')
    
    def create_challenge(self):
        self.challenge = random.randint(10, 20)
        print(f'Created challenge {self.challenge}')
        return json.dumps({'Challenge' : self.challenge})

    def solve_challenge(self, challenge):
        while True:
            key = random.randint(0, 2**32)
            solution = str_bin_in_4digits(hashlib.sha1(str(key).encode()).hexdigest())
            if solution[:challenge] == challenge * '0':
                return str(key)
    
    def check_solution(self, key):
        solution = str_bin_in_4digits(hashlib.sha1(str(key).encode()).hexdigest())
        if solution[:self.challenge] == self.challenge * '0':
                self._is_solved = True
                return True
        else:
            return False
    

    # cryptography
    def get_public_key_hex(self):
        print(self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                    ))
        return self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                    ).hex()

    def get_node_keys(self):
        return self.node_keys

    def get_num_keys(self):
        return len(self.node_keys)

    def add_node_key(self, node_id, pubkey):
        self.node_keys[node_id] = pubkey
    
    def sign_message(self, message):
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    
    def verify_signature(self, node_id, message, signature):
        try:
            self.node_keys[node_id].verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            print(f'valid signature from node {node_id}')
            return True
        except InvalidSignature:
            print(f'invalid signature from node {node_id}')
            return False
