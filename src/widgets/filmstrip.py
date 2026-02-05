"""
Filmstrip Widget
Left panel showing photo thumbnails with state indicators.
"""
from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen

from ..core.state_machine import PhotoState


class ThumbnailWidget(QFrame):
    """Individual thumbnail in the filmstrip."""
    
    clicked = Signal(int)  # Emits index when clicked
    
    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self._pixmap: Optional[QPixmap] = None
        self._state = PhotoState.UNSEEN
        self._is_active = False
        
        self.setFixedSize(100, 70)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("thumbnail")
    
    def set_pixmap(self, pixmap: QPixmap):
        """Set the thumbnail image."""
        self._pixmap = pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )
        self.update()
    
    def set_state(self, state: PhotoState):
        """Update the photo state."""
        self._state = state
        self.update()
    
    def set_active(self, active: bool):
        """Set whether this thumbnail is currently selected."""
        self._is_active = active
        self.update()
    
    def paintEvent(self, event):
        """Paint the thumbnail with state indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background/image
        if self._pixmap:
            # Center crop the image
            x = (self._pixmap.width() - self.width()) // 2
            y = (self._pixmap.height() - self.height()) // 2
            painter.drawPixmap(0, 0, self._pixmap, max(0, x), max(0, y), 
                             self.width(), self.height())
        else:
            painter.fillRect(self.rect(), QColor("#e0dcd7"))
        
        # Apply opacity for rejected photos
        if self._state == PhotoState.REJECTED:
            painter.fillRect(self.rect(), QColor(255, 255, 255, 150))
        
        # Draw selection border
        if self._is_active:
            pen = QPen(QColor("#2d2a26"), 3)
            painter.setPen(pen)
            painter.drawRect(1, 1, self.width() - 2, self.height() - 2)
        elif self._state != PhotoState.UNSEEN:
            pen = QPen(QColor(self._state.color), 2)
            painter.setPen(pen)
            painter.drawRect(1, 1, self.width() - 2, self.height() - 2)
        
        # Draw state indicator dot
        if self._state != PhotoState.UNSEEN:
            indicator_size = 14
            x = self.width() - indicator_size - 4
            y = 4
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(self._state.color))
            painter.drawEllipse(x, y, indicator_size, indicator_size)
            
            # Draw icon in indicator
            painter.setPen(QColor("white"))
            painter.setFont(painter.font())
            icon = "✓" if self._state == PhotoState.KEPT else \
                   "✕" if self._state == PhotoState.REJECTED else "?"
            painter.drawText(x, y, indicator_size, indicator_size, 
                           Qt.AlignCenter, icon)
    
    def mousePressEvent(self, event):
        """Emit clicked signal."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)


class Filmstrip(QScrollArea):
    """
    Scrollable filmstrip showing all photo thumbnails.
    
    Signals:
        photo_selected(int): Emitted when a thumbnail is clicked
    """
    
    photo_selected = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._thumbnails: List[ThumbnailWidget] = []
        self._current_index = 0
        
        # Setup scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setObjectName("filmstrip")
        
        # Container widget
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(6)
        self._layout.addStretch()
        
        self.setWidget(self._container)
        self.setFixedWidth(120)
    
    def set_photos(self, count: int):
        """
        Initialize filmstrip with given number of photos.
        Call load_thumbnail() to set actual images.
        """
        # Clear existing
        self.clear()
        
        # Remove stretch
        if self._layout.count() > 0:
            self._layout.takeAt(self._layout.count() - 1)
        
        # Create thumbnail widgets
        for i in range(count):
            thumb = ThumbnailWidget(i)
            thumb.clicked.connect(self._on_thumbnail_clicked)
            self._thumbnails.append(thumb)
            self._layout.addWidget(thumb)
        
        # Add stretch at end
        self._layout.addStretch()
        
        # Select first
        if self._thumbnails:
            self._thumbnails[0].set_active(True)
    
    def set_thumbnail(self, index: int, pixmap: QPixmap):
        """Set the thumbnail image for a specific index."""
        if 0 <= index < len(self._thumbnails):
            self._thumbnails[index].set_pixmap(pixmap)
    
    def set_photo_state(self, index: int, state: PhotoState):
        """Update the state indicator for a photo."""
        if 0 <= index < len(self._thumbnails):
            self._thumbnails[index].set_state(state)
    
    def set_current_index(self, index: int):
        """Set the currently active photo."""
        if 0 <= index < len(self._thumbnails):
            # Deselect old
            if 0 <= self._current_index < len(self._thumbnails):
                self._thumbnails[self._current_index].set_active(False)
            
            # Select new
            self._current_index = index
            self._thumbnails[index].set_active(True)
            
            # Scroll to visible
            self.ensureWidgetVisible(self._thumbnails[index])
    
    def clear(self):
        """Remove all thumbnails."""
        for thumb in self._thumbnails:
            self._layout.removeWidget(thumb)
            thumb.deleteLater()
        self._thumbnails.clear()
        self._current_index = 0
    
    def _on_thumbnail_clicked(self, index: int):
        """Handle thumbnail click."""
        self.set_current_index(index)
        self.photo_selected.emit(index)
