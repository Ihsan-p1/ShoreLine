"""
Image Analysis
Focus and noise detection with qualitative indicators.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np


@dataclass
class AnalysisResult:
    """Result of image analysis."""
    focus_level: str  # "Low", "Medium", "High"
    focus_explanation: str
    noise_level: str  # "Low", "Medium", "High"
    noise_explanation: str
    
    @property
    def combined_explanation(self) -> str:
        return f"{self.focus_explanation} {self.noise_explanation}"


class ImageAnalyzer:
    """
    Analyzes images for focus quality and noise levels.
    
    Uses:
    - Laplacian variance for focus detection
    - Noise estimation based on high-frequency content
    - ISO/EXIF context when available
    """
    
    # Thresholds (tuned empirically)
    FOCUS_LOW_THRESHOLD = 100
    FOCUS_HIGH_THRESHOLD = 500
    
    NOISE_LOW_THRESHOLD = 5
    NOISE_HIGH_THRESHOLD = 15
    
    def __init__(self):
        pass
    
    def analyze(self, image_path: str | Path, exif: dict = None) -> AnalysisResult:
        """
        Analyze an image for focus and noise.
        
        Args:
            image_path: Path to the image file
            exif: Optional EXIF data for context
        
        Returns:
            AnalysisResult with qualitative indicators
        """
        try:
            # Load image
            img = cv2.imread(str(image_path))
            if img is None:
                return self._default_result("Could not load image")
            
            # Analyze focus
            focus_level, focus_score = self._analyze_focus(img)
            focus_explanation = self._explain_focus(focus_level, focus_score)
            
            # Analyze noise
            noise_level, noise_score = self._analyze_noise(img, exif)
            noise_explanation = self._explain_noise(noise_level, noise_score, exif)
            
            return AnalysisResult(
                focus_level=focus_level,
                focus_explanation=focus_explanation,
                noise_level=noise_level,
                noise_explanation=noise_explanation
            )
            
        except Exception as e:
            return self._default_result(f"Analysis error: {e}")
    
    def _analyze_focus(self, img: np.ndarray) -> Tuple[str, float]:
        """
        Analyze focus using Laplacian variance.
        Higher variance = sharper image.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculate Laplacian
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        # Classify
        if variance < self.FOCUS_LOW_THRESHOLD:
            return "Low", variance
        elif variance > self.FOCUS_HIGH_THRESHOLD:
            return "High", variance
        else:
            return "Medium", variance
    
    def _analyze_noise(self, img: np.ndarray, exif: dict = None) -> Tuple[str, float]:
        """
        Estimate noise level in the image.
        Uses high-frequency content analysis.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float64)
        
        # Estimate noise using median absolute deviation
        # Apply a high-pass filter
        kernel = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]])
        filtered = cv2.filter2D(gray, -1, kernel)
        
        # Calculate noise estimate
        noise_estimate = np.median(np.abs(filtered)) / 0.6745
        
        # Consider ISO if available
        iso = exif.get('iso', 400) if exif else 400
        iso_factor = 1.0
        if iso > 3200:
            iso_factor = 0.7  # Be more lenient at high ISO
        elif iso > 1600:
            iso_factor = 0.85
        
        adjusted_noise = noise_estimate * iso_factor
        
        # Classify
        if adjusted_noise < self.NOISE_LOW_THRESHOLD:
            return "Low", noise_estimate
        elif adjusted_noise > self.NOISE_HIGH_THRESHOLD:
            return "High", noise_estimate
        else:
            return "Medium", noise_estimate
    
    def _explain_focus(self, level: str, score: float) -> str:
        """Generate human-readable focus explanation."""
        explanations = {
            "High": "Sharp focus on subject.",
            "Medium": "Acceptable sharpness, slight softness detected.",
            "Low": "Slight focus miss, possibly motion blur or manual focus error."
        }
        return explanations.get(level, "")
    
    def _explain_noise(self, level: str, score: float, exif: dict = None) -> str:
        """Generate human-readable noise explanation."""
        iso = exif.get('iso') if exif else None
        
        if level == "Low":
            if iso and iso <= 400:
                return "Clean image at base ISO."
            return "Clean image, low noise level."
        elif level == "Medium":
            if iso:
                return f"Moderate noise at ISO {iso}, acceptable for most uses."
            return "Moderate noise, acceptable for most uses."
        else:  # High
            if iso and iso > 1600:
                return f"Higher noise due to ISO {iso}, expected for low-light conditions."
            return "Higher noise detected, may affect fine details."
    
    def _default_result(self, error_msg: str) -> AnalysisResult:
        """Return a default result when analysis fails."""
        return AnalysisResult(
            focus_level="—",
            focus_explanation=error_msg,
            noise_level="—",
            noise_explanation=""
        )
    
    def analyze_center_region(self, image_path: str | Path, region_ratio: float = 0.3) -> dict:
        """
        Analyze only the center region of the image.
        Useful for subject-biased focus detection.
        """
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                return {"error": "Could not load image"}
            
            h, w = img.shape[:2]
            
            # Calculate center region
            center_h = int(h * region_ratio)
            center_w = int(w * region_ratio)
            y1 = (h - center_h) // 2
            y2 = y1 + center_h
            x1 = (w - center_w) // 2
            x2 = x1 + center_w
            
            center_region = img[y1:y2, x1:x2]
            
            focus_level, focus_score = self._analyze_focus(center_region)
            
            return {
                "center_focus_level": focus_level,
                "center_focus_score": focus_score
            }
            
        except Exception as e:
            return {"error": str(e)}
