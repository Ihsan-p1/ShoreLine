"""
Session Management
Handles photo collection, state tracking, and session-scoped undo.
"""
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from .state_machine import PhotoState, StateTransition


@dataclass
class Photo:
    """Represents a single photo in the session."""
    path: Path
    name: str
    state: PhotoState = PhotoState.UNSEEN
    exif: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "name": self.name,
            "state": self.state.name,
            "exif": self.exif
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Photo':
        return cls(
            path=Path(data["path"]),
            name=data["name"],
            state=PhotoState[data["state"]],
            exif=data.get("exif", {})
        )


@dataclass 
class UndoAction:
    """Represents an undoable action."""
    photo_index: int
    old_state: PhotoState
    new_state: PhotoState
    timestamp: datetime = field(default_factory=datetime.now)


class Session:
    """
    Manages a culling session for a folder of photos.
    
    Features:
    - Loads photos from a directory
    - Tracks state for each photo
    - Maintains undo stack (session-scoped)
    - Counts by state
    """
    
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff', '.tif', '.raw', '.cr2', '.nef', '.arw'}
    
    def __init__(self):
        self.session_id: Optional[str] = None
        self.folder_path: Optional[Path] = None
        self.photos: List[Photo] = []
        self.current_index: int = 0
        self.undo_stack: List[UndoAction] = []
        self.is_active: bool = False
        
    @property
    def current_photo(self) -> Optional[Photo]:
        """Get the currently selected photo."""
        if 0 <= self.current_index < len(self.photos):
            return self.photos[self.current_index]
        return None
    
    @property
    def total_count(self) -> int:
        return len(self.photos)
    
    @property
    def kept_count(self) -> int:
        return sum(1 for p in self.photos if p.state == PhotoState.KEPT)
    
    @property
    def rejected_count(self) -> int:
        return sum(1 for p in self.photos if p.state == PhotoState.REJECTED)
    
    @property
    def review_count(self) -> int:
        return sum(1 for p in self.photos if p.state == PhotoState.REVIEW_LATER)
    
    @property
    def decided_count(self) -> int:
        return self.kept_count + self.rejected_count + self.review_count
    
    @property
    def progress_percent(self) -> float:
        if self.total_count == 0:
            return 0.0
        return (self.decided_count / self.total_count) * 100
    
    def load_folder(self, folder_path: str | Path) -> bool:
        """
        Load all images from a folder.
        Returns True if successful.
        """
        folder = Path(folder_path)
        if not folder.is_dir():
            return False
        
        # Find all image files
        image_files = []
        for file in folder.iterdir():
            if file.is_file() and file.suffix.lower() in self.IMAGE_EXTENSIONS:
                image_files.append(file)
        
        if not image_files:
            return False
        
        # Sort by filename
        image_files.sort(key=lambda f: f.name.lower())
        
        # Create photo objects
        self.photos = [
            Photo(path=f, name=f.name)
            for f in image_files
        ]
        
        # Initialize session
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.folder_path = folder
        self.current_index = 0
        self.undo_stack = []
        self.is_active = True
        
        return True
    
    def set_photo_state(self, new_state: PhotoState) -> bool:
        """
        Set the state of the current photo.
        Returns True if state was changed.
        """
        photo = self.current_photo
        if not photo:
            return False
        
        old_state = photo.state
        
        # Check if transition is allowed
        if not StateTransition.can_transition(old_state, new_state):
            return False
        
        # Save to undo stack
        self.undo_stack.append(UndoAction(
            photo_index=self.current_index,
            old_state=old_state,
            new_state=new_state
        ))
        
        # Apply new state
        photo.state = new_state
        return True
    
    def undo(self) -> bool:
        """
        Undo the last action.
        Returns True if undo was performed.
        """
        if not self.undo_stack:
            return False
        
        action = self.undo_stack.pop()
        
        # Restore old state
        if 0 <= action.photo_index < len(self.photos):
            self.photos[action.photo_index].state = action.old_state
            self.current_index = action.photo_index
            return True
        
        return False
    
    def navigate(self, delta: int, accelerated: bool = False) -> bool:
        """
        Navigate to a different photo.
        Returns True if navigation occurred.
        """
        step = delta * (5 if accelerated else 1)
        new_index = self.current_index + step
        new_index = max(0, min(new_index, len(self.photos) - 1))
        
        if new_index != self.current_index:
            self.current_index = new_index
            return True
        return False
    
    def advance_to_next_unseen(self) -> bool:
        """
        Jump to the next unseen photo.
        Returns True if found and navigated.
        """
        for i in range(self.current_index + 1, len(self.photos)):
            if self.photos[i].state == PhotoState.UNSEEN:
                self.current_index = i
                return True
        return False
    
    def get_photo_at(self, index: int) -> Optional[Photo]:
        """Get photo at specific index."""
        if 0 <= index < len(self.photos):
            return self.photos[index]
        return None
    
    def end_session(self):
        """End the current session, clearing undo stack."""
        self.undo_stack.clear()
        self.is_active = False
    
    def save_session(self, filepath: str | Path) -> bool:
        """Save session state to JSON file."""
        try:
            data = {
                "session_id": self.session_id,
                "folder_path": str(self.folder_path),
                "current_index": self.current_index,
                "photos": [p.to_dict() for p in self.photos]
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False
    
    def load_session(self, filepath: str | Path) -> bool:
        """Load session state from JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.session_id = data["session_id"]
            self.folder_path = Path(data["folder_path"])
            self.current_index = data["current_index"]
            self.photos = [Photo.from_dict(p) for p in data["photos"]]
            self.undo_stack = []
            self.is_active = True
            return True
        except Exception:
            return False
