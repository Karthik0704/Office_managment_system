import base64
import json
import random
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io

def generate_dummy_frame(camera_name, width=640, height=480):
    """Generate a dummy camera frame with timestamp and camera name."""
    # Create a blank image
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Add some random shapes to simulate movement
    for _ in range(10):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        draw.rectangle([x1, y1, x2, y2], outline=color)
    
    # Add timestamp and camera name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw.text((10, 10), f"Camera: {camera_name}", fill=(255, 255, 255))
    draw.text((10, 30), f"Time: {timestamp}", fill=(255, 255, 255))
    
    # Convert PIL Image to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_bytes = buffer.getvalue()
    
    # Convert to base64 for easy transmission
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    return {
        'camera_name': camera_name,
        'timestamp': timestamp,
        'frame': img_base64,
        'width': width,
        'height': height
    }

def detect_motion(prev_frame, curr_frame, threshold=30):
    """Simple motion detection by comparing frames."""
    if prev_frame is None or curr_frame is None:
        return False, None
    
    # Convert base64 to numpy arrays
    prev_img_bytes = base64.b64decode(prev_frame['frame'])
    curr_img_bytes = base64.b64decode(curr_frame['frame'])
    
    prev_img = Image.open(io.BytesIO(prev_img_bytes))
    curr_img = Image.open(io.BytesIO(curr_img_bytes))
    
    prev_array = np.array(prev_img.convert('L'))  # Convert to grayscale
    curr_array = np.array(curr_img.convert('L'))
    
    # Calculate absolute difference
    diff = np.abs(prev_array - curr_array)
    
    # Check if difference exceeds threshold
    motion_detected = np.mean(diff) > threshold
    
    # If motion detected, mark the areas of motion
    if motion_detected:
        # Create a mask of areas with significant change
        mask = diff > threshold
        
        # Draw bounding boxes around motion areas
        labeled_img = curr_img.copy()
        draw = ImageDraw.Draw(labeled_img)
        
        # Simplified bounding box (just a demo)
        motion_points = np.where(mask)
        if len(motion_points[0]) > 0:
            y_min, y_max = np.min(motion_points[0]), np.max(motion_points[0])
            x_min, x_max = np.min(motion_points[1]), np.max(motion_points[1])
            
            # Draw rectangle
            draw.rectangle([x_min, y_min, x_max, y_max], outline=(255, 0, 0), width=2)
            
            # Add text
            draw.text((x_min, y_min - 20), "Motion Detected", fill=(255, 0, 0))
            
            # Convert back to base64
            buffer = io.BytesIO()
            labeled_img.save(buffer, format='JPEG')
            img_bytes = buffer.getvalue()
            motion_frame = base64.b64encode(img_bytes).decode('utf-8')
            
            return motion_detected, {
                'frame': motion_frame,
                'bounding_box': {
                    'x': int(x_min),
                    'y': int(y_min),
                    'width': int(x_max - x_min),
                    'height': int(y_max - y_min)
                },
                'confidence': float(np.mean(diff[mask]) / 255)  # Normalize to 0-1
            }
    
    return motion_detected, None
