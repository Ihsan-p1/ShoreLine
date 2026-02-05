"""
ShoreLine Main Application Window
Personal photo culling with keyboard-first workflow.
"""
import shutil
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QFileDialog, QStackedWidget, QPushButton,
    QProgressBar, QMessageBox, QDialog, QLineEdit, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QKeyEvent, QPixmap, QDragEnterEvent, QDropEvent

from .core.state_machine import PhotoState
from .core.session import Session
from .core.image_loader import ImageLoader
from .core.image_analyzer import ImageAnalyzer
from .widgets.photo_viewer import PhotoViewer
from .widgets.filmstrip import Filmstrip
from .widgets.action_bar import ActionBar
from .widgets.tech_overlay import TechOverlay
from .widgets.details_panel import DetailsPanel
from .input.keyboard_handler import KeyboardHandler
from .input.gamepad_handler import GamepadHandler
from .utils.exif_reader import extract_exif


class WelcomeScreen(QWidget):
    """Welcome screen shown before folder import."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("welcome-screen")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Logo/Title container
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setSpacing(8)
        
        # Title
        title = QLabel("ShoreLine")
        title.setObjectName("welcome-title")
        title.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Fast photo culling for photographers")
        subtitle.setObjectName("welcome-subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(subtitle)
        
        layout.addWidget(title_container)
        layout.addSpacing(40)
        
        # Import button
        self.import_btn = QPushButton("Import Folder")
        self.import_btn.setObjectName("import-btn")
        self.import_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.import_btn, alignment=Qt.AlignCenter)
        
        # Hint
        hint = QLabel("Or drag and drop a folder anywhere")
        hint.setObjectName("welcome-hint")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)
        
        layout.addSpacing(60)
        
        # Keyboard guide
        guide_container = QFrame()
        guide_container.setObjectName("keyboard-guide-container")
        guide_layout = QVBoxLayout(guide_container)
        guide_layout.setSpacing(12)
        
        guide_title = QLabel("Keyboard Shortcuts")
        guide_title.setObjectName("guide-title")
        guide_title.setAlignment(Qt.AlignCenter)
        guide_layout.addWidget(guide_title)
        
        shortcuts = [
            ("L", "Keep"),
            ("K", "Review"),
            ("J", "Reject"),
            ("A / D", "Navigate"),
            ("I", "Toggle Info"),
            ("E", "Export Kept"),
        ]
        
        shortcuts_widget = QWidget()
        shortcuts_layout = QHBoxLayout(shortcuts_widget)
        shortcuts_layout.setSpacing(24)
        
        for key, action in shortcuts:
            item = QWidget()
            item_layout = QVBoxLayout(item)
            item_layout.setSpacing(4)
            
            key_label = QLabel(key)
            key_label.setObjectName("shortcut-key")
            key_label.setAlignment(Qt.AlignCenter)
            item_layout.addWidget(key_label)
            
            action_label = QLabel(action)
            action_label.setObjectName("shortcut-action")
            action_label.setAlignment(Qt.AlignCenter)
            item_layout.addWidget(action_label)
            
            shortcuts_layout.addWidget(item)
        
        guide_layout.addWidget(shortcuts_widget)
        layout.addWidget(guide_container)


class ClickableLabel(QLabel):
    """Label that emits a signal when clicked."""
    clicked = Signal()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class StatusBar(QFrame):
    """Top status bar showing filename and progress."""
    
    filter_kept = Signal()
    filter_review = Signal()
    filter_rejected = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("status-bar")
        self.setFixedHeight(56)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # Filename
        self.filename_label = QLabel("—")
        self.filename_label.setObjectName("filename")
        layout.addWidget(self.filename_label)
        
        layout.addStretch()
        
        # Progress
        progress_container = QWidget()
        progress_layout = QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(12)
        
        self.progress_label = QLabel("0 / 0")
        self.progress_label.setObjectName("progress-text")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress-bar")
        self.progress_bar.setFixedWidth(180)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_container)
        layout.addStretch()
        
        # Counts (clickable badges)
        counts_container = QWidget()
        counts_layout = QHBoxLayout(counts_container)
        counts_layout.setContentsMargins(0, 0, 0, 0)
        counts_layout.setSpacing(8)
        
        self.keep_count = ClickableLabel("0")
        self.keep_count.setObjectName("count-keep")
        self.keep_count.setCursor(Qt.PointingHandCursor)
        self.keep_count.setToolTip("Click to show kept photos")
        self.keep_count.clicked.connect(self.filter_kept.emit)
        counts_layout.addWidget(self.keep_count)
        
        self.review_count = ClickableLabel("0")
        self.review_count.setObjectName("count-review")
        self.review_count.setCursor(Qt.PointingHandCursor)
        self.review_count.setToolTip("Click to show photos for review")
        self.review_count.clicked.connect(self.filter_review.emit)
        counts_layout.addWidget(self.review_count)
        
        self.reject_count = ClickableLabel("0")
        self.reject_count.setObjectName("count-reject")
        self.reject_count.setCursor(Qt.PointingHandCursor)
        self.reject_count.setToolTip("Click to show rejected photos")
        self.reject_count.clicked.connect(self.filter_rejected.emit)
        counts_layout.addWidget(self.reject_count)
        
        layout.addWidget(counts_container)
    
    def update_from_session(self, session: Session):
        """Update status bar from session data."""
        if session.current_photo:
            self.filename_label.setText(session.current_photo.name)
        
        self.progress_label.setText(f"{session.current_index + 1} / {session.total_count}")
        self.progress_bar.setMaximum(max(1, session.total_count))
        self.progress_bar.setValue(session.decided_count)
        
        self.keep_count.setText(str(session.kept_count))
        self.review_count.setText(str(session.review_count))
        self.reject_count.setText(str(session.rejected_count))


class ExportDialog(QDialog):
    """Dialog for exporting kept photos."""
    
    def __init__(self, kept_count: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Kept Photos")
        self.setFixedSize(450, 200)
        self.setObjectName("export-dialog")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Info
        info = QLabel(f"You have <b>{kept_count}</b> photos marked as Keep.")
        info.setObjectName("export-info")
        layout.addWidget(info)
        
        # Folder selection
        folder_container = QWidget()
        folder_layout = QHBoxLayout(folder_container)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(12)
        
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select destination folder...")
        self.folder_input.setObjectName("folder-input")
        folder_layout.addWidget(self.folder_input, 1)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("browse-btn")
        browse_btn.clicked.connect(self._browse_folder)
        folder_layout.addWidget(browse_btn)
        
        layout.addWidget(folder_container)
        
        # Buttons
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)
        
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancel-btn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self.export_btn = QPushButton(f"Export {kept_count} Photos")
        self.export_btn.setObjectName("export-btn-action")
        self.export_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.export_btn)
        
        layout.addWidget(btn_container)
        
        self.selected_folder = None
    
    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Export Folder", "",
            QFileDialog.ShowDirsOnly
        )
        if folder:
            self.folder_input.setText(folder)
            self.selected_folder = folder
    
    def get_folder(self) -> Optional[str]:
        return self.folder_input.text() if self.folder_input.text() else None


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ShoreLine")
        self.setMinimumSize(1200, 800)
        
        # Core components
        self.session = Session()
        self.image_loader = ImageLoader(self)
        self.image_analyzer = ImageAnalyzer()
        self.keyboard_handler = KeyboardHandler(self)
        self.gamepad_handler = GamepadHandler(self)
        
        # Filter state
        self._current_filter: Optional[PhotoState] = None
        self._filtered_indices: list = []
        self._details_visible = True
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Start gamepad handler
        self.gamepad_handler.start()
        
        # Toast timer
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._hide_toast)
    
    def _setup_ui(self):
        """Setup the UI layout."""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Stacked widget for welcome/workspace
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # Welcome screen
        self.welcome_screen = WelcomeScreen()
        self.welcome_screen.import_btn.clicked.connect(self._import_folder)
        self.stack.addWidget(self.welcome_screen)
        
        # Workspace
        self.workspace = QWidget()
        self.workspace.setObjectName("workspace")
        workspace_layout = QVBoxLayout(self.workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        
        # Status bar
        self.status_bar = StatusBar()
        workspace_layout.addWidget(self.status_bar)
        
        # Main content area
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Filmstrip (left)
        self.filmstrip = Filmstrip()
        content_layout.addWidget(self.filmstrip)
        
        # Photo viewer container (center)
        viewer_container = QWidget()
        viewer_container.setObjectName("viewer-container")
        viewer_layout = QVBoxLayout(viewer_container)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.photo_viewer = PhotoViewer()
        viewer_layout.addWidget(self.photo_viewer)
        
        # Tech overlay (positioned over viewer)
        self.tech_overlay = TechOverlay(self.photo_viewer)
        
        content_layout.addWidget(viewer_container, 1)
        
        # Details panel (right)
        self.details_panel = DetailsPanel()
        content_layout.addWidget(self.details_panel)
        
        workspace_layout.addWidget(content, 1)
        
        # Action bar
        self.action_bar = ActionBar()
        workspace_layout.addWidget(self.action_bar)
        
        # Toast notification
        self.toast = QLabel("")
        self.toast.setObjectName("toast")
        self.toast.setAlignment(Qt.AlignCenter)
        self.toast.hide()
        
        self.stack.addWidget(self.workspace)
    
    def _connect_signals(self):
        """Connect all signals."""
        # Keyboard
        self.keyboard_handler.action_keep.connect(lambda: self._set_state(PhotoState.KEPT))
        self.keyboard_handler.action_reject.connect(lambda: self._set_state(PhotoState.REJECTED))
        self.keyboard_handler.action_review.connect(lambda: self._set_state(PhotoState.REVIEW_LATER))
        self.keyboard_handler.navigate.connect(self._navigate)
        self.keyboard_handler.toggle_zoom.connect(self.photo_viewer.toggle_zoom)
        self.keyboard_handler.show_tech_info.connect(self._show_tech_info)
        self.keyboard_handler.toggle_details.connect(self._toggle_details)
        self.keyboard_handler.undo.connect(self._undo)
        self.keyboard_handler.advance.connect(self._advance)
        self.keyboard_handler.export_kept.connect(self._export_kept)
        
        # Gamepad
        self.gamepad_handler.action_keep.connect(lambda: self._set_state(PhotoState.KEPT))
        self.gamepad_handler.action_reject.connect(lambda: self._set_state(PhotoState.REJECTED))
        self.gamepad_handler.action_review.connect(lambda: self._set_state(PhotoState.REVIEW_LATER))
        self.gamepad_handler.navigate.connect(lambda d: self._navigate(d, False))
        self.gamepad_handler.toggle_zoom.connect(self.photo_viewer.toggle_zoom)
        self.gamepad_handler.show_tech_info.connect(self._show_tech_info)
        self.gamepad_handler.undo.connect(self._undo)
        
        # Action bar
        self.action_bar.action_triggered.connect(self._set_state)
        
        # Filmstrip
        self.filmstrip.photo_selected.connect(self._go_to_photo)
        
        # Image loader
        self.image_loader.image_loaded.connect(self._on_image_loaded)
        self.image_loader.thumbnail_loaded.connect(self._on_thumbnail_loaded)
        
        # Zoom state
        self.photo_viewer.zoom_changed.connect(self._on_zoom_changed)
        
        # Category filtering
        self.status_bar.filter_kept.connect(lambda: self._filter_by_state(PhotoState.KEPT))
        self.status_bar.filter_review.connect(lambda: self._filter_by_state(PhotoState.REVIEW_LATER))
        self.status_bar.filter_rejected.connect(lambda: self._filter_by_state(PhotoState.REJECTED))
    
    def _toggle_details(self):
        """Toggle details panel visibility."""
        self._details_visible = not self._details_visible
        self.details_panel.setVisible(self._details_visible)
    
    def _import_folder(self):
        """Open folder dialog and import photos."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Photo Folder", "",
            QFileDialog.ShowDirsOnly
        )
        
        if folder:
            self._load_folder(folder)
    
    def _load_folder(self, folder_path: str):
        """Load photos from a folder."""
        if not self.session.load_folder(folder_path):
            QMessageBox.warning(
                self, "No Photos Found",
                "No image files were found in the selected folder."
            )
            return
        
        # Switch to workspace
        self.stack.setCurrentWidget(self.workspace)
        
        # Setup filmstrip
        self.filmstrip.set_photos(self.session.total_count)
        
        # Load thumbnails and EXIF
        for i, photo in enumerate(self.session.photos):
            self.image_loader.load_thumbnail(photo.path)
            photo.exif = extract_exif(photo.path)
        
        # Display first photo
        self._display_current_photo()
    
    def _display_current_photo(self):
        """Display the current photo."""
        photo = self.session.current_photo
        if not photo:
            return
        
        # Load full image
        self.image_loader.load_image(photo.path, priority=True)
        
        # Update UI
        self.filmstrip.set_current_index(self.session.current_index)
        self.status_bar.update_from_session(self.session)
        
        # Update details panel
        self.details_panel.update_details(photo.path, photo.exif)
        
        # Preload nearby images
        paths = [p.path for p in self.session.photos]
        self.image_loader.preload_around(paths, self.session.current_index)
    
    def _on_image_loaded(self, path: str, pixmap: QPixmap):
        """Handle loaded image."""
        if self.session.current_photo and str(self.session.current_photo.path) == path:
            self.photo_viewer.set_image(pixmap)
    
    def _on_thumbnail_loaded(self, path: str, pixmap: QPixmap):
        """Handle loaded thumbnail."""
        for i, photo in enumerate(self.session.photos):
            if str(photo.path) == path:
                self.filmstrip.set_thumbnail(i, pixmap)
                break
    
    def _set_state(self, state: PhotoState):
        """Set state for current photo."""
        if not self.session.is_active:
            return
        
        if self.session.set_photo_state(state):
            # Update filmstrip
            self.filmstrip.set_photo_state(self.session.current_index, state)
            self.status_bar.update_from_session(self.session)
            
            # Auto-advance
            self._navigate(1, False)
    
    def _navigate(self, direction: int, accelerated: bool):
        """Navigate to another photo."""
        if self._current_filter:
            self._navigate_filtered(direction)
        else:
            if self.session.navigate(direction, accelerated):
                self._display_current_photo()
    
    def _navigate_filtered(self, direction: int):
        """Navigate within filtered photos."""
        if not self._filtered_indices:
            return
        
        try:
            current_pos = self._filtered_indices.index(self.session.current_index)
            new_pos = current_pos + direction
            if 0 <= new_pos < len(self._filtered_indices):
                self.session.current_index = self._filtered_indices[new_pos]
                self._display_current_photo()
        except ValueError:
            if self._filtered_indices:
                self.session.current_index = self._filtered_indices[0]
                self._display_current_photo()
    
    def _filter_by_state(self, state: PhotoState):
        """Filter photos by state."""
        if self._current_filter == state:
            self._current_filter = None
            self._filtered_indices = []
            self.setWindowTitle("ShoreLine")
        else:
            self._current_filter = state
            self._filtered_indices = [
                i for i, p in enumerate(self.session.photos)
                if p.state == state
            ]
            
            if not self._filtered_indices:
                QMessageBox.information(
                    self, "No Photos",
                    f"No photos marked as {state.display_name}."
                )
                self._current_filter = None
                return
            
            self.setWindowTitle(f"ShoreLine — {state.display_name} ({len(self._filtered_indices)})")
            self.session.current_index = self._filtered_indices[0]
            self._display_current_photo()
    
    def _go_to_photo(self, index: int):
        """Go to a specific photo."""
        if self.session.get_photo_at(index):
            self.session.current_index = index
            self._display_current_photo()
    
    def _advance(self):
        """Advance to next unseen photo."""
        if self.session.advance_to_next_unseen():
            self._display_current_photo()
    
    def _undo(self):
        """Undo last action."""
        if self.session.undo():
            self.filmstrip.set_photo_state(
                self.session.current_index,
                self.session.current_photo.state
            )
            self.status_bar.update_from_session(self.session)
            self._display_current_photo()
            self._show_toast("Action undone")
    
    def _export_kept(self):
        """Export kept photos to a folder."""
        kept_count = self.session.kept_count
        if kept_count == 0:
            QMessageBox.information(
                self, "No Photos to Export",
                "You haven't marked any photos as Keep yet."
            )
            return
        
        dialog = ExportDialog(kept_count, self)
        if dialog.exec() == QDialog.Accepted:
            folder = dialog.get_folder()
            if folder:
                self._do_export(folder)
    
    def _do_export(self, folder: str):
        """Actually export the kept photos."""
        dest_path = Path(folder)
        if not dest_path.exists():
            dest_path.mkdir(parents=True)
        
        exported = 0
        for photo in self.session.photos:
            if photo.state == PhotoState.KEPT:
                src = Path(photo.path)
                dst = dest_path / src.name
                
                # Handle duplicate names
                counter = 1
                while dst.exists():
                    dst = dest_path / f"{src.stem}_{counter}{src.suffix}"
                    counter += 1
                
                try:
                    shutil.copy2(src, dst)
                    exported += 1
                except Exception as e:
                    print(f"Error copying {src}: {e}")
        
        self._show_toast(f"Exported {exported} photos to {dest_path.name}")
    
    def _show_toast(self, message: str):
        """Show a toast notification."""
        self.toast.setText(message)
        self.toast.show()
        self._toast_timer.start(2000)
    
    def _hide_toast(self):
        """Hide the toast."""
        self.toast.hide()
    
    def _show_tech_info(self, show: bool):
        """Show or hide technical info overlay."""
        if show and self.session.current_photo:
            result = self.image_analyzer.analyze(
                self.session.current_photo.path,
                self.session.current_photo.exif
            )
            self.tech_overlay.update_analysis(result)
            self.tech_overlay.show()
            self.tech_overlay.move(20, self.photo_viewer.height() - self.tech_overlay.height() - 20)
        else:
            self.tech_overlay.hide()
    
    def _on_zoom_changed(self, zoomed: bool):
        """Handle zoom state change."""
        if zoomed:
            self._show_tech_info(True)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press."""
        if event.key() == Qt.Key_Escape and self._current_filter:
            self._current_filter = None
            self._filtered_indices = []
            self.setWindowTitle("ShoreLine")
            return
        
        if not self.keyboard_handler.handle_key_press(event):
            super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event: QKeyEvent):
        """Handle key release."""
        if not self.keyboard_handler.handle_key_release(event):
            super().keyReleaseEvent(event)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop."""
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if Path(path).is_dir():
                self._load_folder(path)
    
    def closeEvent(self, event):
        """Clean up on close."""
        self.gamepad_handler.stop()
        self.image_loader.shutdown()
        super().closeEvent(event)
