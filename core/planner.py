"""Planner boundary: turns language into allow-listed structured operations."""
from core.nlu import RuleBasedNLU

class Planner:
    def __init__(self): self._nlu = RuleBasedNLU()
    def plan(self, command: str): return self._nlu.parse(command)
