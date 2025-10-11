import pytest

from processors.state_machine import StateMachine, StateTransition


class TestStateMachine:
    """Test cases for StateMachine class."""
    
    @pytest.fixture
    def state_machine(self):
        """Create a state machine instance."""
        sm = StateMachine(initial_state="idle")
        sm.add_transition("idle", "active")
        sm.add_transition("active", "complete")
        sm.add_transition("active", "failed")
        return sm
    
    def test_initialization(self, state_machine):
        """Test state machine initializes correctly."""
        assert state_machine.current_state == "idle"
        assert state_machine.initial_state == "idle"
    
    def test_add_transition(self):
        """Test adding transitions."""
        sm = StateMachine(initial_state="start")
        sm.add_transition("start", "middle")
        sm.add_transition("middle", "end")
        
        assert "middle" in sm.allowed_transitions["start"]
        assert "end" in sm.allowed_transitions["middle"]
    
    def test_can_transition_valid(self, state_machine):
        """Test checking valid transition."""
        assert state_machine.can_transition("active") is True
    
    def test_can_transition_invalid(self, state_machine):
        """Test checking invalid transition."""
        assert state_machine.can_transition("complete") is False
    
    def test_transition_success(self, state_machine):
        """Test successful transition."""
        result = state_machine.transition("active")
        assert result is True
        assert state_machine.current_state == "active"
    
    def test_transition_failure(self, state_machine):
        """Test failed transition."""
        result = state_machine.transition("complete")
        assert result is False
        assert state_machine.current_state == "idle"
    
    def test_transition_with_condition(self, state_machine):
        """Test transition with condition."""
        state_machine.transition("active", condition="manual trigger")
        history = state_machine.get_history()
        
        assert len(history) == 1
        assert history[0].condition == "manual trigger"
    
    def test_get_history(self, state_machine):
        """Test getting transition history."""
        state_machine.transition("active")
        state_machine.transition("complete")
        
        history = state_machine.get_history()
        assert len(history) == 2
        assert history[0].from_state == "idle"
        assert history[0].to_state == "active"
        assert history[1].from_state == "active"
        assert history[1].to_state == "complete"
    
    def test_reset(self, state_machine):
        """Test resetting state machine."""
        state_machine.transition("active")
        state_machine.transition("complete")
        
        state_machine.reset()
        
        assert state_machine.current_state == "idle"
        assert len(state_machine.get_history()) == 0
