"""
Photo State Machine
Each photo can be in ONE state only.
"""
from enum import Enum, auto


class PhotoState(Enum):
    """Possible states for each photo in the session."""
    UNSEEN = auto()
    KEPT = auto()
    REJECTED = auto()
    REVIEW_LATER = auto()
    
    def __str__(self):
        return self.name.replace('_', ' ').title()
    
    @property
    def display_name(self):
        """Human-readable name for UI display."""
        names = {
            PhotoState.UNSEEN: "",
            PhotoState.KEPT: "Kept",
            PhotoState.REJECTED: "Rejected",
            PhotoState.REVIEW_LATER: "Review"
        }
        return names.get(self, "")
    
    @property
    def color(self):
        """Color associated with this state."""
        colors = {
            PhotoState.UNSEEN: "#8a8580",
            PhotoState.KEPT: "#4a9e6b",
            PhotoState.REJECTED: "#c45d5d",
            PhotoState.REVIEW_LATER: "#c49a3d"
        }
        return colors.get(self, "#8a8580")


class StateTransition:
    """
    Handles state transition rules.
    
    Rules:
    - UNSEEN can transition to any decided state
    - REVIEW_LATER can transition to KEPT or REJECTED
    - KEPT and REJECTED cannot transition directly to each other
    - Any state can revert to previous via undo
    """
    
    ALLOWED_TRANSITIONS = {
        PhotoState.UNSEEN: {PhotoState.KEPT, PhotoState.REJECTED, PhotoState.REVIEW_LATER},
        PhotoState.REVIEW_LATER: {PhotoState.KEPT, PhotoState.REJECTED},
        PhotoState.KEPT: set(),  # Cannot transition directly
        PhotoState.REJECTED: set(),  # Cannot transition directly
    }
    
    @classmethod
    def can_transition(cls, from_state: PhotoState, to_state: PhotoState) -> bool:
        """Check if transition is allowed."""
        if from_state == to_state:
            return False
        allowed = cls.ALLOWED_TRANSITIONS.get(from_state, set())
        return to_state in allowed
    
    @classmethod
    def get_allowed_transitions(cls, from_state: PhotoState) -> set:
        """Get all allowed transitions from a state."""
        return cls.ALLOWED_TRANSITIONS.get(from_state, set())
