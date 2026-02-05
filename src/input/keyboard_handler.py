"""
Keyboard Handler
Maps keyboard input to application actions.
"""
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QKeyEvent

from ..core.state_machine import PhotoState


class KeyboardHandler(QObject):
    """
    Handles keyboard input and emits corresponding action signals.
    
    Keyboard Mapping:
    - J = Reject
    - K = Review
    - L = Keep
    - A / Left Arrow = Previous photo
    - D / Right Arrow = Next photo
    - W = Toggle zoom
    - S = Show tech info (hold)
    - I = Toggle details panel
    - U = Undo
    - E = Export kept photos
    - Space = Advance to next unseen
    - Shift = Accelerated navigation
    
    Signals:
        action_keep: Keep current photo
        action_reject: Reject current photo
        action_review: Mark for review
        navigate(int, bool): Navigate (direction, accelerated)
        toggle_zoom: Toggle 100% zoom
        show_tech_info(bool): Show/hide tech overlay
        toggle_details: Toggle details panel
        undo: Undo last action
        advance: Advance to next unseen
        export_kept: Export kept photos
    """
    
    action_keep = Signal()
    action_reject = Signal()
    action_review = Signal()
    navigate = Signal(int, bool)  # direction, accelerated
    toggle_zoom = Signal()
    show_tech_info = Signal(bool)
    toggle_details = Signal()
    undo = Signal()
    advance = Signal()
    export_kept = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._shift_held = False
        self._s_held = False
    
    def handle_key_press(self, event: QKeyEvent) -> bool:
        """
        Handle a key press event.
        Returns True if the event was handled.
        """
        key = event.key()
        modifiers = event.modifiers()
        self._shift_held = bool(modifiers & Qt.ShiftModifier)
        
        # Decision keys
        if key == Qt.Key_L:
            self.action_keep.emit()
            return True
        
        if key == Qt.Key_K:
            self.action_review.emit()
            return True
        
        if key == Qt.Key_J:
            self.action_reject.emit()
            return True
        
        # Navigation
        if key in (Qt.Key_A, Qt.Key_Left):
            self.navigate.emit(-1, self._shift_held)
            return True
        
        if key in (Qt.Key_D, Qt.Key_Right):
            self.navigate.emit(1, self._shift_held)
            return True
        
        # Zoom
        if key == Qt.Key_W:
            self.toggle_zoom.emit()
            return True
        
        # Tech info (hold S)
        if key == Qt.Key_S and not self._s_held:
            self._s_held = True
            self.show_tech_info.emit(True)
            return True
        
        # Toggle details panel
        if key == Qt.Key_I:
            self.toggle_details.emit()
            return True
        
        # Undo
        if key == Qt.Key_U:
            self.undo.emit()
            return True
        
        # Export kept photos
        if key == Qt.Key_E:
            self.export_kept.emit()
            return True
        
        # Advance to next unseen
        if key == Qt.Key_Space:
            self.advance.emit()
            return True
        
        return False
    
    def handle_key_release(self, event: QKeyEvent) -> bool:
        """
        Handle a key release event.
        Returns True if the event was handled.
        """
        key = event.key()
        
        # Release tech info on S release
        if key == Qt.Key_S and self._s_held:
            self._s_held = False
            self.show_tech_info.emit(False)
            return True
        
        # Track shift release
        if key == Qt.Key_Shift:
            self._shift_held = False
        
        return False
