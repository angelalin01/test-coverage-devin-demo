from typing import Dict, List, Optional, Callable
from datetime import datetime
from pydantic import BaseModel


class StateTransition(BaseModel):
    """Represents a state transition."""
    from_state: str
    to_state: str
    condition: Optional[str] = None
    timestamp: Optional[datetime] = None


class StateMachine:
    """
    Generic state machine for managing milestone transitions.
    """
    
    def __init__(self, initial_state: str):
        self.current_state = initial_state
        self.initial_state = initial_state
        self.allowed_transitions: Dict[str, List[str]] = {}
        self.transition_history: List[StateTransition] = []
        self.transition_callbacks: Dict[str, List[Callable]] = {}
    
    def add_transition(self, from_state: str, to_state: str) -> None:
        """
        Add an allowed state transition.
        
        Args:
            from_state: The source state
            to_state: The target state
        """
        if from_state not in self.allowed_transitions:
            self.allowed_transitions[from_state] = []
        
        if to_state not in self.allowed_transitions[from_state]:
            self.allowed_transitions[from_state].append(to_state)
    
    def can_transition(self, to_state: str) -> bool:
        """
        Check if transition to a state is allowed from current state.
        
        Args:
            to_state: The target state
            
        Returns:
            True if transition is allowed
        """
        if self.current_state not in self.allowed_transitions:
            return False
        
        return to_state in self.allowed_transitions[self.current_state]
    
    def transition(self, to_state: str, condition: Optional[str] = None) -> bool:
        """
        Transition to a new state if allowed.
        
        Args:
            to_state: The target state
            condition: Optional condition description
            
        Returns:
            True if transition was successful
        """
        if not self.can_transition(to_state):
            return False
        
        transition = StateTransition(
            from_state=self.current_state,
            to_state=to_state,
            condition=condition,
            timestamp=datetime.now()
        )
        
        self.transition_history.append(transition)
        self.current_state = to_state
        
        if to_state in self.transition_callbacks:
            for callback in self.transition_callbacks[to_state]:
                callback(transition)
        
        return True
    
    def register_callback(self, state: str, callback: Callable) -> None:
        """
        Register a callback for when entering a specific state.
        
        Args:
            state: The state to trigger on
            callback: Callback function
        """
        if state not in self.transition_callbacks:
            self.transition_callbacks[state] = []
        
        self.transition_callbacks[state].append(callback)
    
    def get_history(self) -> List[StateTransition]:
        """
        Get the transition history.
        
        Returns:
            List of state transitions
        """
        return list(self.transition_history)
    
    def reset(self) -> None:
        """Reset the state machine to initial state."""
        self.current_state = self.initial_state
        self.transition_history.clear()
