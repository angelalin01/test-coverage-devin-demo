import pytest
from datetime import datetime

from processors.state_machine import StateMachine, StateTransition


class TestStateMachine:
    
    @pytest.fixture
    def state_machine(self):
        return StateMachine(initial_state="idle")
    
    def test_initialization(self, state_machine):
        assert state_machine.current_state == "idle"
        assert state_machine.initial_state == "idle"
        assert len(state_machine.allowed_transitions) == 0
        assert len(state_machine.transition_history) == 0
    
    def test_add_transition(self, state_machine):
        state_machine.add_transition("idle", "running")
        
        assert "idle" in state_machine.allowed_transitions
        assert "running" in state_machine.allowed_transitions["idle"]
    
    def test_add_multiple_transitions_from_same_state(self, state_machine):
        state_machine.add_transition("idle", "running")
        state_machine.add_transition("idle", "stopped")
        
        assert len(state_machine.allowed_transitions["idle"]) == 2
        assert "running" in state_machine.allowed_transitions["idle"]
        assert "stopped" in state_machine.allowed_transitions["idle"]
    
    def test_add_duplicate_transition(self, state_machine):
        state_machine.add_transition("idle", "running")
        state_machine.add_transition("idle", "running")
        
        assert state_machine.allowed_transitions["idle"].count("running") == 1
    
    def test_can_transition_valid(self, state_machine):
        state_machine.add_transition("idle", "running")
        
        assert state_machine.can_transition("running") is True
    
    def test_can_transition_invalid(self, state_machine):
        state_machine.add_transition("idle", "running")
        
        assert state_machine.can_transition("stopped") is False
    
    def test_can_transition_no_transitions_defined(self, state_machine):
        assert state_machine.can_transition("running") is False
    
    def test_transition_success(self, state_machine):
        state_machine.add_transition("idle", "running")
        
        result = state_machine.transition("running")
        
        assert result is True
        assert state_machine.current_state == "running"
        assert len(state_machine.transition_history) == 1
    
    def test_transition_failure(self, state_machine):
        state_machine.add_transition("idle", "running")
        
        result = state_machine.transition("stopped")
        
        assert result is False
        assert state_machine.current_state == "idle"
        assert len(state_machine.transition_history) == 0
    
    def test_transition_with_condition(self, state_machine):
        state_machine.add_transition("idle", "running")
        
        result = state_machine.transition("running", condition="temperature > 100")
        
        assert result is True
        assert state_machine.transition_history[0].condition == "temperature > 100"
    
    def test_transition_history_tracking(self, state_machine):
        state_machine.add_transition("idle", "running")
        state_machine.add_transition("running", "stopped")
        
        state_machine.transition("running", condition="start command")
        state_machine.transition("stopped", condition="stop command")
        
        assert len(state_machine.transition_history) == 2
        assert state_machine.transition_history[0].from_state == "idle"
        assert state_machine.transition_history[0].to_state == "running"
        assert state_machine.transition_history[1].from_state == "running"
        assert state_machine.transition_history[1].to_state == "stopped"
    
    def test_register_callback(self, state_machine):
        callback_executed = []
        
        def callback(transition):
            callback_executed.append(transition.to_state)
        
        state_machine.register_callback("running", callback)
        state_machine.add_transition("idle", "running")
        state_machine.transition("running")
        
        assert len(callback_executed) == 1
        assert callback_executed[0] == "running"
    
    def test_multiple_callbacks_same_state(self, state_machine):
        executions = []
        
        def callback1(transition):
            executions.append("callback1")
        
        def callback2(transition):
            executions.append("callback2")
        
        state_machine.register_callback("running", callback1)
        state_machine.register_callback("running", callback2)
        state_machine.add_transition("idle", "running")
        state_machine.transition("running")
        
        assert len(executions) == 2
        assert executions == ["callback1", "callback2"]
    
    def test_callback_not_executed_on_failed_transition(self, state_machine):
        callback_executed = []
        
        def callback(transition):
            callback_executed.append(True)
        
        state_machine.register_callback("running", callback)
        
        state_machine.transition("running")
        
        assert len(callback_executed) == 0
    
    def test_get_history(self, state_machine):
        state_machine.add_transition("idle", "running")
        state_machine.add_transition("running", "stopped")
        
        state_machine.transition("running")
        state_machine.transition("stopped")
        
        history = state_machine.get_history()
        assert len(history) == 2
        assert isinstance(history[0], StateTransition)
    
    def test_reset(self, state_machine):
        state_machine.add_transition("idle", "running")
        state_machine.transition("running")
        
        state_machine.reset()
        
        assert state_machine.current_state == "idle"
        assert len(state_machine.transition_history) == 0
    
    def test_complex_transition_chain(self, state_machine):
        state_machine.add_transition("idle", "initializing")
        state_machine.add_transition("initializing", "ready")
        state_machine.add_transition("ready", "running")
        state_machine.add_transition("running", "stopped")
        
        assert state_machine.transition("initializing") is True
        assert state_machine.transition("ready") is True
        assert state_machine.transition("running") is True
        assert state_machine.transition("stopped") is True
        
        assert state_machine.current_state == "stopped"
        assert len(state_machine.transition_history) == 4


class TestStateTransition:
    
    def test_state_transition_creation(self):
        transition = StateTransition(
            from_state="idle",
            to_state="running",
            condition="start command",
            timestamp=datetime.now()
        )
        
        assert transition.from_state == "idle"
        assert transition.to_state == "running"
        assert transition.condition == "start command"
        assert transition.timestamp is not None
    
    def test_state_transition_optional_fields(self):
        transition = StateTransition(
            from_state="idle",
            to_state="running"
        )
        
        assert transition.condition is None
        assert transition.timestamp is None
