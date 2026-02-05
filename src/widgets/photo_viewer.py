"""
Photo Viewer Widget
Main display area for the current photo with zoom support.
"""
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea
from PySide6.QtCore import Qt, Signal, QPoint, QSize
from PySide6.QtGui import QPixmap, QPainter, QWheelEvent, QMouseEvent


class PhotoViewer(QWidget):
    """
    Main photo display widget with zoom and pan support.
    
    Signals:
        zoom_changed(bool): Emitted when zoom state changes (True = zoomed, False = fit)
    """
    
    zoom_changed = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: Optional[QPixmap] = None
        self._scaled_pixmap: Optional[QPixmap] = None
        self._zoom_factor = 1.0
        self._is_zoomed = False
        self._pan_start = QPoint()
        self._pan_offset = QPoint(0, 0)
        self._dragging = False
        
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        
    def set_image(self, pixmap: QPixmap):
        """Set the image to display."""
        self._pixmap = pixmap
        self._reset_view()
        self.update()
    
    def set_image_from_path(self, path: str | Path):
        """Load and display an image from a file path."""
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            self.set_image(pixmap)
    
    def clear(self):
        """Clear the current image."""
        self._pixmap = None
        self._scaled_pixmap = None
        self.update()
    
    def _reset_view(self):
        """Reset to fit-in-view mode."""
        self._zoom_factor = 1.0
        self._is_zoomed = False
        self._pan_offset = QPoint(0, 0)
        self._update_scaled_pixmap()
        self.zoom_changed.emit(False)
    
    def toggle_zoom(self):
        """Toggle between fit-to-view and 100% zoom."""
        if self._pixmap is None:
            return
        
        if self._is_zoomed:
            # Return to fit view
            self._reset_view()
        else:
            # Zoom to 100%
            self._zoom_factor = 1.0
            self._is_zoomed = True
            self._pan_offset = QPoint(0, 0)
            self._scaled_pixmap = self._pixmap
            self.zoom_changed.emit(True)
        
        self.update()
    
    def is_zoomed(self) -> bool:
        """Check if currently zoomed."""
        return self._is_zoomed
    
    def _update_scaled_pixmap(self):
        """Update the scaled pixmap for fit-to-view mode."""
        if self._pixmap is None:
            self._scaled_pixmap = None
            return
        
        if self._is_zoomed:
            self._scaled_pixmap = self._pixmap
        else:
            # Fit to widget size while maintaining aspect ratio
            available_size = self.size()
            self._scaled_pixmap = self._pixmap.scaled(
                available_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
    
    def paintEvent(self, event):
        """Paint the photo."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Draw background
        painter.fillRect(self.rect(), Qt.transparent)
        
        if self._scaled_pixmap is None:
            # Draw placeholder
            painter.setPen(Qt.gray)
            painter.drawText(self.rect(), Qt.AlignCenter, "No image loaded")
            return
        
        # Calculate position to center the image
        x = (self.width() - self._scaled_pixmap.width()) // 2 + self._pan_offset.x()
        y = (self.height() - self._scaled_pixmap.height()) // 2 + self._pan_offset.y()
        
        painter.drawPixmap(x, y, self._scaled_pixmap)
    
    def resizeEvent(self, event):
        """Handle widget resize."""
        super().resizeEvent(event)
        self._update_scaled_pixmap()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Start panning when zoomed."""
        if event.button() == Qt.LeftButton and self._is_zoomed:
            self._dragging = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle panning."""
        if self._dragging and self._is_zoomed:
            delta = event.pos() - self._pan_start
            self._pan_offset += delta
            self._pan_start = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Stop panning."""
        if event.button() == Qt.LeftButton:
            self._dragging = False
            if self._is_zoomed:
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Toggle zoom on double-click."""
        if event.button() == Qt.LeftButton:
            self.toggle_zoom()
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle scroll wheel for zoom."""
        if self._is_zoomed:
            # Pan with scroll wheel when zoomed
            delta = event.angleDelta()
            self._pan_offset += QPoint(delta.x() // 4, delta.y() // 4)
            self.update()
