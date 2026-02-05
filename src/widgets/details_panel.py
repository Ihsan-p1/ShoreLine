"""
Details Panel Widget
Shows comprehensive EXIF and file information.
"""
import os
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QScrollArea
)
from PySide6.QtCore import Qt


class DetailRow(QWidget):
    """Single row in the details panel."""
    
    def __init__(self, label: str, value: str = "—", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)
        
        self.label = QLabel(label)
        self.label.setObjectName("detail-label")
        self.label.setFixedWidth(100)
        layout.addWidget(self.label)
        
        self.value = QLabel(value)
        self.value.setObjectName("detail-value")
        self.value.setAlignment(Qt.AlignRight)
        layout.addWidget(self.value, 1)
    
    def set_value(self, value: str):
        self.value.setText(value if value else "—")


class DetailsPanel(QFrame):
    """
    Panel showing comprehensive photo details.
    
    Displays:
    - File info (type, size, location)
    - Date taken
    - Dimensions
    - Camera info (maker, model)
    - Exposure settings (F-stop, shutter, ISO)
    - Focal length
    - Metering mode
    - Flash mode
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("details-panel")
        self.setFixedWidth(280)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)
        
        # Header
        header = QLabel("Details")
        header.setObjectName("details-header")
        layout.addWidget(header)
        
        layout.addSpacing(12)
        
        # File info section
        self.row_type = DetailRow("Type")
        layout.addWidget(self.row_type)
        
        self.row_size = DetailRow("Size")
        layout.addWidget(self.row_size)
        
        self.row_location = DetailRow("File location")
        self.row_location.value.setWordWrap(True)
        layout.addWidget(self.row_location)
        
        self.row_date = DetailRow("Date taken")
        layout.addWidget(self.row_date)
        
        self.row_dimensions = DetailRow("Dimensions")
        layout.addWidget(self.row_dimensions)
        
        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setObjectName("detail-separator")
        layout.addWidget(sep1)
        layout.addSpacing(8)
        
        # Camera info
        self.row_camera_maker = DetailRow("Camera maker")
        layout.addWidget(self.row_camera_maker)
        
        self.row_camera_model = DetailRow("Camera model")
        layout.addWidget(self.row_camera_model)
        
        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setObjectName("detail-separator")
        layout.addWidget(sep2)
        layout.addSpacing(8)
        
        # Exposure settings
        self.row_fstop = DetailRow("F-stop")
        layout.addWidget(self.row_fstop)
        
        self.row_exposure = DetailRow("Exposure time")
        layout.addWidget(self.row_exposure)
        
        self.row_iso = DetailRow("ISO speed")
        layout.addWidget(self.row_iso)
        
        self.row_exposure_bias = DetailRow("Exposure bias")
        layout.addWidget(self.row_exposure_bias)
        
        self.row_focal = DetailRow("Focal length")
        layout.addWidget(self.row_focal)
        
        self.row_metering = DetailRow("Metering mode")
        layout.addWidget(self.row_metering)
        
        self.row_flash = DetailRow("Flash mode")
        layout.addWidget(self.row_flash)
        
        layout.addStretch()
    
    def update_details(self, photo_path: Path, exif: dict):
        """Update panel with photo information."""
        # File info
        try:
            stat = photo_path.stat()
            size_bytes = stat.st_size
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
            
            self.row_size.set_value(size_str)
        except:
            self.row_size.set_value("—")
        
        # File type
        ext = photo_path.suffix.upper().replace('.', '')
        self.row_type.set_value(f"{ext} File")
        
        # File location (truncate if too long)
        location = str(photo_path.parent)
        if len(location) > 30:
            location = "..." + location[-27:]
        self.row_location.set_value(location)
        
        # From EXIF
        if exif:
            # Date taken
            date_str = exif.get("date_taken", "")
            if date_str:
                try:
                    # Parse common EXIF date format
                    dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    self.row_date.set_value(dt.strftime("%m/%d/%Y %I:%M %p"))
                except:
                    self.row_date.set_value(date_str)
            else:
                self.row_date.set_value("—")
            
            # Dimensions
            dims = exif.get("dimensions")
            if dims:
                self.row_dimensions.set_value(dims)
            else:
                self.row_dimensions.set_value("—")
            
            # Camera
            self.row_camera_maker.set_value(exif.get("camera_make", ""))
            self.row_camera_model.set_value(exif.get("camera_model", ""))
            
            # Exposure
            aperture = exif.get("aperture")
            if aperture:
                self.row_fstop.set_value(f"f/{aperture:.1f}" if isinstance(aperture, float) else f"f/{aperture}")
            else:
                self.row_fstop.set_value("—")
            
            shutter = exif.get("shutter_speed")
            if shutter:
                self.row_exposure.set_value(f"{shutter} sec." if "sec" not in str(shutter).lower() else shutter)
            else:
                self.row_exposure.set_value("—")
            
            iso = exif.get("iso")
            if iso:
                self.row_iso.set_value(f"ISO-{iso}")
            else:
                self.row_iso.set_value("—")
            
            self.row_exposure_bias.set_value(exif.get("exposure_bias", "0 step"))
            
            focal = exif.get("focal_length")
            if focal:
                self.row_focal.set_value(f"{focal:.0f} mm" if isinstance(focal, float) else f"{focal} mm")
            else:
                self.row_focal.set_value("—")
            
            self.row_metering.set_value(exif.get("metering_mode", "—"))
            self.row_flash.set_value(exif.get("flash_mode", "—"))
        else:
            # Clear EXIF fields
            self.row_date.set_value("—")
            self.row_dimensions.set_value("—")
            self.row_camera_maker.set_value("—")
            self.row_camera_model.set_value("—")
            self.row_fstop.set_value("—")
            self.row_exposure.set_value("—")
            self.row_iso.set_value("—")
            self.row_exposure_bias.set_value("—")
            self.row_focal.set_value("—")
            self.row_metering.set_value("—")
            self.row_flash.set_value("—")
    
    def clear(self):
        """Clear all values."""
        for row in [self.row_type, self.row_size, self.row_location, 
                    self.row_date, self.row_dimensions, self.row_camera_maker,
                    self.row_camera_model, self.row_fstop, self.row_exposure,
                    self.row_iso, self.row_exposure_bias, self.row_focal,
                    self.row_metering, self.row_flash]:
            row.set_value("—")
