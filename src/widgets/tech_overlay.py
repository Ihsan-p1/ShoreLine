"""
Technical Info Overlay
Shows focus and noise analysis on demand.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

from ..core.image_analyzer import AnalysisResult


class TechOverlay(QFrame):
    """
    Semi-transparent overlay showing technical image analysis.
    
    Displays:
    - Focus quality (Low/Medium/High)
    - Noise level (Low/Medium/High)
    - Human-readable explanations
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tech-overlay")
        self.setFixedWidth(280)
        
        # Make overlay float over content
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Focus row
        focus_row = QHBoxLayout()
        focus_label = QLabel("Focus")
        focus_label.setObjectName("tech-label")
        self.focus_value = QLabel("—")
        self.focus_value.setObjectName("tech-value")
        focus_row.addWidget(focus_label)
        focus_row.addStretch()
        focus_row.addWidget(self.focus_value)
        layout.addLayout(focus_row)
        
        # Noise row
        noise_row = QHBoxLayout()
        noise_label = QLabel("Noise")
        noise_label.setObjectName("tech-label")
        self.noise_value = QLabel("—")
        self.noise_value.setObjectName("tech-value")
        noise_row.addWidget(noise_label)
        noise_row.addStretch()
        noise_row.addWidget(self.noise_value)
        layout.addLayout(noise_row)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("tech-separator")
        layout.addWidget(separator)
        
        # Explanation
        self.explanation = QLabel("")
        self.explanation.setObjectName("tech-explanation")
        self.explanation.setWordWrap(True)
        layout.addWidget(self.explanation)
        
        # Hidden by default
        self.hide()
    
    def update_analysis(self, result: AnalysisResult):
        """Update the overlay with new analysis results."""
        self.focus_value.setText(result.focus_level)
        self._set_level_style(self.focus_value, result.focus_level)
        
        self.noise_value.setText(result.noise_level)
        self._set_level_style(self.noise_value, result.noise_level)
        
        self.explanation.setText(result.combined_explanation)
    
    def _set_level_style(self, label: QLabel, level: str):
        """Apply color styling based on level."""
        level_lower = level.lower()
        # Remove old classes
        label.setProperty("level", level_lower)
        label.style().unpolish(label)
        label.style().polish(label)
    
    def clear(self):
        """Clear the overlay content."""
        self.focus_value.setText("—")
        self.noise_value.setText("—")
        self.explanation.setText("")
