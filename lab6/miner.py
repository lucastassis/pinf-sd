import random
import json
import hashlib
import queue

# From https://codereview.stackexchange.com/a/260276
def str_bin_in_4digits(hex_string: str) -> str:
    """
    Turn a hex string into a binary string.
    In the output string, binary digits are space separated in groups of 4.
    >>> str_bin_in_4digits('20AC')
    '0010000010101100'
    """

    return f"{int(hex_string,16):0{len(hex_string)*5-1}_b}".replace('_', '')

class Miner():
    def __init__(self):
        self.id = random.randint(0, 65335)
        self.miner_list = [self.id]
        self.vote = random.randint(0, 65335)
        self.voter_list = {str(self.id) : self.vote}
        self._is_leader = False
        self._is_solved = False
        self.challenge = 0

    # getters and setters
    def get_id(self):
        return self.id
    
    def get_vote(self):
        return self.vote
    
    def get_num_miners(self):
        return len(self.miner_list)
    
    def is_leader(self):
        return self._is_leader

    def is_solved(self):
        return self._is_solved
    
    def set_is_solved(self):
        self._is_solved = True
    
    def get_num_voters(self):
        return len(self.voter_list)
    
    def add_miner_init(self, new_id):
        if new_id not in self.miner_list:
            self.miner_list.append(new_id)
    
    def add_miner_voting(self, vote):
        self.voter_list.update({vote['ClientID'] : vote['VoteID']})
    
    # ops
    def election(self):
        winner = max(self.voter_list)
        if int(winner) == self.id:
            self._is_leader = True
        else:
            self._is_leader = False
    
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
