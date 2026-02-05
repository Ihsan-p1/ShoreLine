"""
EXIF Metadata Reader
Extracts camera settings from image files.
"""
from pathlib import Path
from typing import Dict, Any, Optional

from PIL import Image, ExifTags

try:
    import exifread
    HAS_EXIFREAD = True
except ImportError:
    HAS_EXIFREAD = False


def extract_exif(image_path: str | Path) -> Dict[str, Any]:
    """
    Extract relevant EXIF data from an image.
    
    Returns:
        Dictionary with ISO, aperture, shutter speed, focal length, camera info
    """
    result = {
        "iso": None,
        "aperture": None,
        "shutter_speed": None,
        "focal_length": None,
        "camera_make": None,
        "camera_model": None,
        "lens": None,
        "date_taken": None,
        "dimensions": None,
        "metering_mode": None,
        "flash_mode": None,
        "exposure_bias": None,
    }
    
    # First, get dimensions from PIL (most reliable)
    try:
        with Image.open(image_path) as img:
            result["dimensions"] = f"{img.width} x {img.height}"
    except:
        pass
    
    if HAS_EXIFREAD:
        try:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
            
            # ISO
            iso_tag = tags.get('EXIF ISOSpeedRatings')
            if iso_tag:
                result["iso"] = int(str(iso_tag))
            
            # Aperture (F-number)
            aperture_tag = tags.get('EXIF FNumber')
            if aperture_tag:
                result["aperture"] = _parse_rational(str(aperture_tag))
            
            # Shutter speed
            shutter_tag = tags.get('EXIF ExposureTime')
            if shutter_tag:
                result["shutter_speed"] = str(shutter_tag)
            
            # Focal length
            focal_tag = tags.get('EXIF FocalLength')
            if focal_tag:
                result["focal_length"] = _parse_rational(str(focal_tag))
            
            # Camera info
            make_tag = tags.get('Image Make')
            if make_tag:
                result["camera_make"] = str(make_tag).strip()
            
            model_tag = tags.get('Image Model')
            if model_tag:
                result["camera_model"] = str(model_tag).strip()
            
            # Lens (if available)
            lens_tag = tags.get('EXIF LensModel')
            if lens_tag:
                result["lens"] = str(lens_tag).strip()
            
            # Date taken
            date_tag = tags.get('EXIF DateTimeOriginal')
            if date_tag:
                result["date_taken"] = str(date_tag)
            
            # Metering mode
            metering_tag = tags.get('EXIF MeteringMode')
            if metering_tag:
                metering_val = str(metering_tag)
                metering_modes = {
                    '0': 'Unknown',
                    '1': 'Average',
                    '2': 'Center-weighted',
                    '3': 'Spot',
                    '4': 'Multi-spot',
                    '5': 'Pattern',
                    '6': 'Partial',
                }
                result["metering_mode"] = metering_modes.get(metering_val, metering_val)
            
            # Flash mode
            flash_tag = tags.get('EXIF Flash')
            if flash_tag:
                flash_val = int(str(flash_tag)) if str(flash_tag).isdigit() else 0
                if flash_val == 0:
                    result["flash_mode"] = "No flash, compulsory"
                elif flash_val & 1:
                    result["flash_mode"] = "Flash fired"
                else:
                    result["flash_mode"] = "No flash"
            
            # Exposure bias
            exp_bias_tag = tags.get('EXIF ExposureBiasValue')
            if exp_bias_tag:
                bias = _parse_rational(str(exp_bias_tag))
                if bias is not None:
                    result["exposure_bias"] = f"{bias:+.1f} step" if bias != 0 else "0 step"
        
        except Exception as e:
            print(f"Error reading EXIF from {image_path}: {e}")
    
    return result


def _parse_rational(value: str) -> Optional[float]:
    """Parse a rational number string like '28/10' to float."""
    try:
        if '/' in value:
            num, denom = value.split('/')
            return float(num) / float(denom)
        return float(value)
    except (ValueError, ZeroDivisionError):
        return None


def format_exif_summary(exif: Dict[str, Any]) -> str:
    """
    Format EXIF data as a short summary string.
    Example: "ISO 400 | f/2.8 | 1/125s | 50mm"
    """
    parts = []
    
    if exif.get("iso"):
        parts.append(f"ISO {exif['iso']}")
    
    if exif.get("aperture"):
        parts.append(f"f/{exif['aperture']:.1f}")
    
    if exif.get("shutter_speed"):
        parts.append(exif["shutter_speed"])
    
    if exif.get("focal_length"):
        parts.append(f"{exif['focal_length']:.0f}mm")
    
    return " | ".join(parts) if parts else "No EXIF data"
