"""
Async Image Loader
Handles efficient loading and caching of images for fast navigation.
Includes EXIF orientation correction.
"""
from pathlib import Path
from typing import Optional, Dict
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from PySide6.QtCore import QObject, Signal, QSize
from PySide6.QtGui import QPixmap, QImage
from PIL import Image, ExifTags
import io


class ImageCache:
    """LRU-style cache for loaded images."""
    
    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self._cache: Dict[str, QPixmap] = {}
        self._order: list = []
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[QPixmap]:
        with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                self._order.remove(key)
                self._order.append(key)
                return self._cache[key]
        return None
    
    def put(self, key: str, pixmap: QPixmap):
        with self._lock:
            if key in self._cache:
                self._order.remove(key)
            elif len(self._cache) >= self.max_size:
                # Remove least recently used
                oldest = self._order.pop(0)
                del self._cache[oldest]
            
            self._cache[key] = pixmap
            self._order.append(key)
    
    def clear(self):
        with self._lock:
            self._cache.clear()
            self._order.clear()


def apply_exif_orientation(img: Image.Image) -> Image.Image:
    """
    Apply EXIF orientation to image.
    This corrects photos that appear rotated.
    """
    try:
        # Get EXIF data
        exif = img._getexif()
        if exif is None:
            return img
        
        # Find orientation tag
        orientation_key = None
        for key, val in ExifTags.TAGS.items():
            if val == 'Orientation':
                orientation_key = key
                break
        
        if orientation_key is None or orientation_key not in exif:
            return img
        
        orientation = exif[orientation_key]
        
        # Apply rotation/flip based on orientation value
        if orientation == 2:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        elif orientation == 3:
            img = img.rotate(180, expand=True)
        elif orientation == 4:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        elif orientation == 5:
            img = img.transpose(Image.FLIP_LEFT_RIGHT).rotate(270, expand=True)
        elif orientation == 6:
            img = img.rotate(270, expand=True)
        elif orientation == 7:
            img = img.transpose(Image.FLIP_LEFT_RIGHT).rotate(90, expand=True)
        elif orientation == 8:
            img = img.rotate(90, expand=True)
        
        return img
    except Exception:
        return img


class ImageLoader(QObject):
    """
    Asynchronous image loader with caching.
    
    Signals:
        image_loaded(str, QPixmap): Emitted when an image is loaded
        thumbnail_loaded(str, QPixmap): Emitted when a thumbnail is loaded
    """
    
    image_loaded = Signal(str, QPixmap)
    thumbnail_loaded = Signal(str, QPixmap)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._full_cache = ImageCache(max_size=10)
        self._thumb_cache = ImageCache(max_size=100)
        self._thumbnail_size = QSize(200, 140)  # Larger thumbnails for better quality
    
    def load_image(self, path: str | Path, priority: bool = False):
        """
        Load a full-resolution image asynchronously.
        
        Args:
            path: Path to the image file
            priority: If True, load immediately in main thread
        """
        path_str = str(path)
        
        # Check cache first
        cached = self._full_cache.get(path_str)
        if cached:
            self.image_loaded.emit(path_str, cached)
            return
        
        if priority:
            # Load synchronously for priority images
            pixmap = self._load_pixmap(path_str, full_size=True)
            if pixmap:
                self._full_cache.put(path_str, pixmap)
                self.image_loaded.emit(path_str, pixmap)
        else:
            # Load asynchronously
            self._executor.submit(self._async_load_image, path_str)
    
    def load_thumbnail(self, path: str | Path):
        """Load a thumbnail asynchronously."""
        path_str = str(path)
        
        # Check cache first
        cached = self._thumb_cache.get(path_str)
        if cached:
            self.thumbnail_loaded.emit(path_str, cached)
            return
        
        # Load asynchronously
        self._executor.submit(self._async_load_thumbnail, path_str)
    
    def _async_load_image(self, path: str):
        """Background image loading."""
        pixmap = self._load_pixmap(path, full_size=True)
        if pixmap:
            self._full_cache.put(path, pixmap)
            self.image_loaded.emit(path, pixmap)
    
    def _async_load_thumbnail(self, path: str):
        """Background thumbnail loading."""
        pixmap = self._load_pixmap(path, full_size=False)
        if pixmap:
            self._thumb_cache.put(path, pixmap)
            self.thumbnail_loaded.emit(path, pixmap)
    
    def _load_pixmap(self, path: str, full_size: bool = True) -> Optional[QPixmap]:
        """Load image and convert to QPixmap with EXIF orientation correction."""
        try:
            # Use PIL for better format support
            with Image.open(path) as img:
                # Apply EXIF orientation FIRST (before any conversion)
                img = apply_exif_orientation(img)
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                if not full_size:
                    # Create thumbnail with higher quality
                    img.thumbnail(
                        (self._thumbnail_size.width(), self._thumbnail_size.height()),
                        Image.Resampling.LANCZOS
                    )
                
                # Convert to QPixmap via bytes
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=95)  # Higher quality for thumbnails too
                buffer.seek(0)
                
                qimage = QImage()
                qimage.loadFromData(buffer.read())
                
                return QPixmap.fromImage(qimage)
                
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            return None
    
    def preload_around(self, paths: list, current_index: int, radius: int = 3):
        """
        Preload images around the current index for smooth navigation.
        """
        for i in range(max(0, current_index - radius), 
                       min(len(paths), current_index + radius + 1)):
            if i != current_index:
                self.load_image(paths[i], priority=False)
    
    def clear_cache(self):
        """Clear all cached images."""
        self._full_cache.clear()
        self._thumb_cache.clear()
    
    def shutdown(self):
        """Shutdown the executor."""
        self._executor.shutdown(wait=False)
