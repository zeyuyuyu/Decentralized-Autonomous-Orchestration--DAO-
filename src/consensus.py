from typing import List, Dict, Set
from dataclasses import dataclass
from enum import Enum
import time
import hashlib

class ConsensusState(Enum):
    PROPOSE = 'PROPOSE'
    PREVOTE = 'PREVOTE'
    PRECOMMIT = 'PRECOMMIT'
    COMMIT = 'COMMIT'

@dataclass
class ConsensusMessage:
    state: ConsensusState
    round: int
    value: str
    validator: str
    signature: str

class BFTConsensus:
    def __init__(self, validators: List[str], fault_tolerance: int):
        self.validators = set(validators)
        self.f = fault_tolerance # Max Byzantine faults tolerated
        self.round = 0
        self.state = ConsensusState.PROPOSE
        self.proposals: Dict[int, str] = {}
        self.prevotes: Dict[int, Dict[str, Set[str]]] = {}
        self.precommits: Dict[int, Dict[str, Set[str]]] = {}
        self.commits: Dict[int, str] = {}
        
    def propose(self, value: str, validator: str) -> ConsensusMessage:
        """Create a proposal for the current round"""
        if validator not in self.validators:
            raise ValueError(f"Invalid validator {validator}")
            
        if self.round in self.proposals:
            raise ValueError(f"Proposal already exists for round {self.round}")
            
        signature = self._sign_message(value, validator)
        self.proposals[self.round] = value
        
        return ConsensusMessage(
            state=ConsensusState.PROPOSE,
            round=self.round,
            value=value,
            validator=validator,
            signature=signature
        )
    
    def prevote(self, proposal: ConsensusMessage, validator: str) -> ConsensusMessage:
        """Cast a prevote for a proposal"""
        if validator not in self.validators:
            raise ValueError(f"Invalid validator {validator}")
            
        if proposal.round not in self.proposals:
            raise ValueError(f"No proposal exists for round {proposal.round}")
            
        if proposal.round not in self.prevotes:
            self.prevotes[proposal.round] = {}
        if proposal.value not in self.prevotes[proposal.round]:
            self.prevotes[proposal.round][proposal.value] = set()
            
        signature = self._sign_message(proposal.value, validator)
        self.prevotes[proposal.round][proposal.value].add(validator)
        
        return ConsensusMessage(
            state=ConsensusState.PREVOTE,
            round=proposal.round,
            value=proposal.value,
            validator=validator,
            signature=signature
        )
    
    def precommit(self, prevote: ConsensusMessage, validator: str) -> ConsensusMessage:
        """Cast a precommit vote if sufficient prevotes received"""
        if validator not in self.validators:
            raise ValueError(f"Invalid validator {validator}")
            
        round_prevotes = self.prevotes.get(prevote.round, {})
        prevote_count = len(round_prevotes.get(prevote.value, set()))
        
        if prevote_count < 2 * self.f + 1:
            raise ValueError(f"Insufficient prevotes ({prevote_count}) for value {prevote.value}")
            
        if prevote.round not in self.precommits:
            self.precommits[prevote.round] = {}
        if prevote.value not in self.precommits[prevote.round]:
            self.precommits[prevote.round][prevote.value] = set()
            
        signature = self._sign_message(prevote.value, validator)
        self.precommits[prevote.round][prevote.value].add(validator)
        
        return ConsensusMessage(
            state=ConsensusState.PRECOMMIT,
            round=prevote.round, 
            value=prevote.value,
            validator=validator,
            signature=signature
        )
    
    def commit(self, precommit: ConsensusMessage, validator: str) -> ConsensusMessage:
        """Commit a value if sufficient precommits received"""
        if validator not in self.validators:
            raise ValueError(f"Invalid validator {validator}")
            
        round_precommits = self.precommits.get(precommit.round, {})
        precommit_count = len(round_precommits.get(precommit.value, set()))
        
        if precommit_count < 2 * self.f + 1:
            raise ValueError(f"Insufficient precommits ({precommit_count}) for value {precommit.value}")
            
        signature = self._sign_message(precommit.value, validator)
        self.commits[precommit.round] = precommit.value
        
        # Advance to next round after commit
        self.round += 1
        
        return ConsensusMessage(
            state=ConsensusState.COMMIT,
            round=precommit.round,
            value=precommit.value,
            validator=validator, 
            signature=signature
        )
        
    def _sign_message(self, value: str, validator: str) -> str:
        """Create signature for message (simplified)"""
        message = f"{value}{validator}{time.time()}"
        return hashlib.sha256(message.encode()).hexdigest()
        
    def get_committed_value(self, round: int) -> str:
        """Get the committed value for a specific round"""
        if round not in self.commits:
            raise ValueError(f"No committed value for round {round}")
        return self.commits[round]