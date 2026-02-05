"""
Gamepad Handler
Maps gamepad input to application actions using pygame.
"""
from typing import Optional, Dict
from threading import Thread, Event
import time

from PySide6.QtCore import QObject, Signal

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


class GamepadHandler(QObject):
    """
    Handles gamepad input using pygame.
    
    Xbox Controller Mapping:
    - A = Keep
    - B = Reject
    - Y = Review
    - LB = Undo
    - RB = Skip/Next
    - LT = Show tech info (hold)
    - RT = Zoom (toggle)
    - D-pad = Navigate
    
    Signals:
        action_keep: Keep current photo
        action_reject: Reject current photo
        action_review: Mark for review
        navigate(int): Navigate direction (-1 or 1)
        toggle_zoom: Toggle zoom
        show_tech_info(bool): Show/hide tech overlay
        undo: Undo last action
        connected(str): Gamepad connected (name)
        disconnected: Gamepad disconnected
    """
    
    action_keep = Signal()
    action_reject = Signal()
    action_review = Signal()
    navigate = Signal(int)
    toggle_zoom = Signal()
    show_tech_info = Signal(bool)
    undo = Signal()
    connected = Signal(str)
    disconnected = Signal()
    
    # Xbox button indices (may vary by controller)
    BTN_A = 0
    BTN_B = 1
    BTN_X = 2
    BTN_Y = 3
    BTN_LB = 4
    BTN_RB = 5
    
    # Trigger axes
    AXIS_LT = 4  # Left trigger
    AXIS_RT = 5  # Right trigger
    
    # D-pad (hat)
    HAT_INDEX = 0
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._joystick: Optional[pygame.joystick.Joystick] = None
        self._running = False
        self._stop_event = Event()
        self._poll_thread: Optional[Thread] = None
        self._last_buttons: Dict[int, bool] = {}
        self._lt_held = False
        self._rt_pressed = False
    
    def start(self):
        """Start listening for gamepad input."""
        if not HAS_PYGAME:
            print("pygame not installed, gamepad support disabled")
            return
        
        pygame.init()
        pygame.joystick.init()
        
        self._running = True
        self._stop_event.clear()
        self._poll_thread = Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
    
    def stop(self):
        """Stop listening for gamepad input."""
        self._running = False
        self._stop_event.set()
        if self._poll_thread:
            self._poll_thread.join(timeout=1.0)
        
        if HAS_PYGAME:
            pygame.joystick.quit()
    
    def _poll_loop(self):
        """Main polling loop for gamepad input."""
        while self._running and not self._stop_event.is_set():
            try:
                pygame.event.pump()
                
                # Check for controllers
                joystick_count = pygame.joystick.get_count()
                
                if joystick_count > 0 and self._joystick is None:
                    # Connect to first available controller
                    self._joystick = pygame.joystick.Joystick(0)
                    self._joystick.init()
                    self.connected.emit(self._joystick.get_name())
                elif joystick_count == 0 and self._joystick is not None:
                    # Controller disconnected
                    self._joystick = None
                    self._last_buttons.clear()
                    self.disconnected.emit()
                
                if self._joystick:
                    self._process_input()
                
            except Exception as e:
                print(f"Gamepad error: {e}")
            
            time.sleep(0.016)  # ~60Hz polling
    
    def _process_input(self):
        """Process current gamepad state."""
        if not self._joystick:
            return
        
        # Read button states
        buttons = {
            i: self._joystick.get_button(i)
            for i in range(self._joystick.get_numbuttons())
        }
        
        # Button press detection (rising edge)
        def pressed(btn_id: int) -> bool:
            current = buttons.get(btn_id, False)
            previous = self._last_buttons.get(btn_id, False)
            return current and not previous
        
        # A = Keep
        if pressed(self.BTN_A):
            self.action_keep.emit()
        
        # B = Reject
        if pressed(self.BTN_B):
            self.action_reject.emit()
        
        # Y = Review
        if pressed(self.BTN_Y):
            self.action_review.emit()
        
        # LB = Undo
        if pressed(self.BTN_LB):
            self.undo.emit()
        
        # RB = Skip/Next
        if pressed(self.BTN_RB):
            self.navigate.emit(1)
        
        # Triggers (analog)
        if self._joystick.get_numaxes() > max(self.AXIS_LT, self.AXIS_RT):
            lt_value = self._joystick.get_axis(self.AXIS_LT)
            rt_value = self._joystick.get_axis(self.AXIS_RT)
            
            # LT = Tech info (threshold-based hold)
            lt_pressed = lt_value > 0.5
            if lt_pressed != self._lt_held:
                self._lt_held = lt_pressed
                self.show_tech_info.emit(lt_pressed)
            
            # RT = Zoom toggle (threshold-based)
            rt_pressed = rt_value > 0.5
            if rt_pressed and not self._rt_pressed:
                self.toggle_zoom.emit()
            self._rt_pressed = rt_pressed
        
        # D-pad navigation
        if self._joystick.get_numhats() > 0:
            hat = self._joystick.get_hat(self.HAT_INDEX)
            if hat[0] == -1:  # Left
                self.navigate.emit(-1)
            elif hat[0] == 1:  # Right
                self.navigate.emit(1)
        
        self._last_buttons = buttons
