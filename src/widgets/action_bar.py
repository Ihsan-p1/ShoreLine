"""
Action Bar Widget
Bottom bar with Keep, Review, Reject buttons.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal

from ..core.state_machine import PhotoState


class ActionButton(QPushButton):
    """Styled action button with icon and keyboard hint."""
    
    def __init__(self, text: str, icon: str, shortcut: str, color: str, parent=None):
        super().__init__(parent)
        self.setText(f"{icon}  {text}")
        self.setObjectName(f"action-{text.lower()}")
        self.setCursor(Qt.PointingHandCursor)
        
        # Store color for styling
        self._color = color
        self._shortcut = shortcut
        
        self.setMinimumWidth(100)
        self.setMinimumHeight(48)


class ActionBar(QFrame):
    """
    Bottom action bar with decision buttons.
    
    Signals:
        action_triggered(PhotoState): Emitted when an action button is clicked
    """
    
    action_triggered = Signal(PhotoState)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("action-bar")
        self.setFixedHeight(72)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(16)
        
        # Center the buttons
        layout.addStretch()
        
        # Reject button
        self.btn_reject = ActionButton(
            "Reject", "✕", "J", 
            PhotoState.REJECTED.color
        )
        self.btn_reject.setObjectName("btn-reject")
        self.btn_reject.clicked.connect(lambda: self.action_triggered.emit(PhotoState.REJECTED))
        layout.addWidget(self.btn_reject)
        
        # Review button
        self.btn_review = ActionButton(
            "Review", "?", "K",
            PhotoState.REVIEW_LATER.color
        )
        self.btn_review.setObjectName("btn-review")
        self.btn_review.clicked.connect(lambda: self.action_triggered.emit(PhotoState.REVIEW_LATER))
        layout.addWidget(self.btn_review)
        
        # Keep button
        self.btn_keep = ActionButton(
            "Keep", "✓", "L",
            PhotoState.KEPT.color
        )
        self.btn_keep.setObjectName("btn-keep")
        self.btn_keep.clicked.connect(lambda: self.action_triggered.emit(PhotoState.KEPT))
        layout.addWidget(self.btn_keep)
        
        layout.addStretch()
