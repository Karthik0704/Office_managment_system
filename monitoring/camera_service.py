import cv2
import numpy as np
import base64
import time
from datetime import datetime
from io import BytesIO
from PIL import Image
import threading
import logging
import requests
from .models import Camera, MotionEvent
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)

class CameraService:
    def __init__(self):
        self.active_streams = {}
        self.frame_buffers = {}
        self.stop_events = {}
    
    def get_camera_stream_url(self, camera_id):
        """Get the stream URL for a camera."""
        try:
            camera = Camera.objects.get(id=camera_id)
            return camera.stream_url
        except Camera.DoesNotExist:
            logger.error(f"Camera with ID {camera_id} does not exist")
            return None
    
    def start_camera_stream(self, camera_id):
        """Start streaming from a camera."""
        if camera_id in self.active_streams:
            logger.info(f"Stream for camera {camera_id} already active")
            return True
        
        stream_url = self.get_camera_stream_url(camera_id)
        if not stream_url:
            return False
        
        # Create a stop event for this stream
        self.stop_events[camera_id] = threading.Event()
        
        # Initialize frame buffer for this camera
        self.frame_buffers[camera_id] = None
        
        # Start stream in a separate thread
        thread = threading.Thread(
            target=self._stream_camera, 
            args=(camera_id, stream_url, self.stop_events[camera_id])
        )
        thread.daemon = True
        thread.start()
        
        self.active_streams[camera_id] = thread
        logger.info(f"Started stream for camera {camera_id}")
        return True
    
    def stop_camera_stream(self, camera_id):
        """Stop streaming from a camera."""
        if camera_id not in self.active_streams:
            logger.info(f"No active stream for camera {camera_id}")
            return False
        
        # Signal the thread to stop
        self.stop_events[camera_id].set()
        
        # Wait for thread to finish
        self.active_streams[camera_id].join(timeout=5.0)
        
        # Clean up
        del self.active_streams[camera_id]
        del self.stop_events[camera_id]
        if camera_id in self.frame_buffers:
            del self.frame_buffers[camera_id]
        
        logger.info(f"Stopped stream for camera {camera_id}")
        return True
    
    def get_latest_frame(self, camera_id):
        """Get the latest frame from a camera."""
        if camera_id not in self.frame_buffers or self.frame_buffers[camera_id] is None:
            logger.warning(f"No frame available for camera {camera_id}")
            return None
        
        return self.frame_buffers[camera_id]
    
    def _stream_camera(self, camera_id, stream_url, stop_event):
        """Stream from a camera and process frames."""
        try:
            # Check if this is a special testing URL
            if stream_url == "TEST_SIMULATOR":
                self._simulate_camera_stream(camera_id, stop_event)
                return
            elif stream_url.startswith("PUBLIC:"):
                self._stream_public_camera(camera_id, stream_url.replace("PUBLIC:", ""), stop_event)
                return
            elif stream_url.startswith("PHONE:"):
                self._stream_phone_camera(camera_id, stream_url.replace("PHONE:", ""), stop_event)
                return
            
            # For real cameras, use OpenCV
            cap = cv2.VideoCapture(stream_url)
            
            if not cap.isOpened():
                logger.error(f"Could not open stream for camera {camera_id}")
                return
            
            prev_frame = None
            motion_detected = False
            motion_frames = []
            
            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Failed to read frame from camera {camera_id}")
                    time.sleep(1)  # Wait before trying again
                    continue
                
                # Process the frame (resize, convert color, etc.)
                frame = cv2.resize(frame, (640, 480))
                
                # Convert to RGB for PIL
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Store the frame in the buffer
                self.frame_buffers[camera_id] = {
                    'frame': self._encode_frame(rgb_frame),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Motion detection
                if prev_frame is not None:
                    motion_detected, confidence = self._detect_motion(prev_frame, rgb_frame)
                    if motion_detected:
                        logger.info(f"Motion detected on camera {camera_id} with confidence {confidence}")
                        motion_frames.append((rgb_frame, confidence))
                        
                        # If we have enough motion frames, save an event
                        if len(motion_frames) >= 5:
                            self._save_motion_event(camera_id, motion_frames)
                            motion_frames = []
                    else:
                        # Reset motion frames if no motion
                        motion_frames = []
                
                prev_frame = rgb_frame
                time.sleep(0.1)  # Limit frame rate
            
            cap.release()
            logger.info(f"Camera {camera_id} stream released")
            
        except Exception as e:
            logger.error(f"Error in camera stream {camera_id}: {str(e)}")
    
    def _simulate_camera_stream(self, camera_id, stop_event):
        """Simulate a camera stream for testing."""
        logger.info(f"Starting simulated stream for camera {camera_id}")
        
        width, height = 640, 480
        prev_frame = None
        motion_frames = []
        
        while not stop_event.is_set():
            # Create a blank image
            img = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(img, f"Camera {camera_id} - {timestamp}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add some random shapes to simulate movement
            for _ in range(5):
                # Random rectangle
                x1 = np.random.randint(0, width)
                y1 = np.random.randint(0, height)
                x2 = np.random.randint(0, width)
                y2 = np.random.randint(0, height)
                color = tuple(np.random.randint(0, 255, 3).tolist())
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            
            # Store the frame in the buffer
            self.frame_buffers[camera_id] = {
                'frame': self._encode_frame(img),
                'timestamp': timestamp
            }
            
            # Motion detection
            if prev_frame is not None:
                motion_detected, confidence = self._detect_motion(prev_frame, img)
                if motion_detected:
                    logger.info(f"Motion detected on simulated camera {camera_id} with confidence {confidence}")
                    motion_frames.append((img, confidence))
                    
                    # If we have enough motion frames, save an event
                    if len(motion_frames) >= 5:
                        self._save_motion_event(camera_id, motion_frames)
                        motion_frames = []
                else:
                    # Reset motion frames if no motion
                    motion_frames = []
            
            prev_frame = img
            time.sleep(0.5)  # Slower frame rate for simulation
    
    def _stream_public_camera(self, camera_id, camera_url, stop_event):
        """Stream from a public camera URL."""
        logger.info(f"Starting public camera stream for camera {camera_id} from {camera_url}")
        
        prev_frame = None
        motion_frames = []
        
        while not stop_event.is_set():
            try:
                # For public cameras, we might need to fetch individual frames
                response = requests.get(camera_url, timeout=5)
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch public camera image: {response.status_code}")
                    time.sleep(2)
                    continue
                
                # Convert to OpenCV format
                img_array = np.frombuffer(response.content, dtype=np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                
                if img is None:
                    logger.warning("Failed to decode image")
                    time.sleep(2)
                    continue
                
                # Resize for consistency
                img = cv2.resize(img, (640, 480))
                
                # Store the frame in the buffer
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.frame_buffers[camera_id] = {
                    'frame': self._encode_frame(img),
                    'timestamp': timestamp
                }
                
                # Motion detection
                if prev_frame is not None:
                    motion_detected, confidence = self._detect_motion(prev_frame, img)
                    if motion_detected:
                        logger.info(f"Motion detected on public camera {camera_id} with confidence {confidence}")
                        motion_frames.append((img, confidence))
                        
                        # If we have enough motion frames, save an event
                        if len(motion_frames) >= 5:
                            self._save_motion_event(camera_id, motion_frames)
                            motion_frames = []
                    else:
                        # Reset motion frames if no motion
                        motion_frames = []
                
                prev_frame = img
                
            except Exception as e:
                logger.error(f"Error fetching public camera image: {str(e)}")
            
            time.sleep(1)  # Public cameras often have rate limits
    
    def _stream_phone_camera(self, camera_id, phone_url, stop_event):
        """Stream from a phone camera using an IP webcam app."""
        logger.info(f"Starting phone camera stream for camera {camera_id} from {phone_url}")
        
        # For phone cameras using IP Webcam app, the URL is typically:
        # http://phone_ip:port/video
        stream_url = phone_url
        if not stream_url.endswith('/video'):
            stream_url = f"{stream_url.rstrip('/')}/video"
        
        cap = cv2.VideoCapture(stream_url)
        
        if not cap.isOpened():
            logger.error(f"Could not open phone camera stream: {stream_url}")
            return
        
        prev_frame = None
        motion_frames = []
        
        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to read frame from phone camera")
                time.sleep(1)
                continue
            
            # Resize for consistency
            frame = cv2.resize(frame, (640, 480))
            
            # Store the frame in the buffer
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.frame_buffers[camera_id] = {
                'frame': self._encode_frame(frame),
                'timestamp': timestamp
            }
            
            # Motion detection
            if prev_frame is not None:
                motion_detected, confidence = self._detect_motion(prev_frame, frame)
                if motion_detected:
                    logger.info(f"Motion detected on phone camera {camera_id} with confidence {confidence}")
                    motion_frames.append((frame, confidence))
                    
                    # If we have enough motion frames, save an event
                    if len(motion_frames) >= 5:
                        self._save_motion_event(camera_id, motion_frames)
                        motion_frames = []
                else:
                    # Reset motion frames if no motion
                    motion_frames = []
            
            prev_frame = frame
            time.sleep(0.1)
        
        cap.release()
        logger.info(f"Phone camera {camera_id} stream released")
    
    def _encode_frame(self, frame):
        """Encode a frame as base64 for transmission."""
        # Convert to PIL Image
        if isinstance(frame, np.ndarray):
            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if frame.shape[2] == 3 else frame)
        else:
            pil_img = frame
            
        buffer = BytesIO()
        pil_img.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _detect_motion(self, prev_frame, curr_frame, threshold=30):
        """Detect motion between frames."""
        # Convert to grayscale
        if isinstance(prev_frame, np.ndarray) and len(prev_frame.shape) == 3:
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        else:
            prev_gray = prev_frame
            
        if isinstance(curr_frame, np.ndarray) and len(curr_frame.shape) == 3:
            curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        else:
            curr_gray = curr_frame
        
        # Calculate absolute difference
        frame_diff = cv2.absdiff(prev_gray, curr_gray)
        
        # Apply threshold
        _, thresh = cv2.threshold(frame_diff, threshold, 255, cv2.THRESH_BINARY)
        
        # Dilate to fill in holes
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter by area
        significant_motion = False
        confidence = 0.0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Minimum area threshold
                significant_motion = True
                confidence = min(1.0, area / 10000)  # Normalize confidence
                break
        
        return significant_motion, confidence
    
    def _save_motion_event(self, camera_id, motion_frames):
        """Save a motion event to the database."""
        try:
            camera = Camera.objects.get(id=camera_id)
            
            # Get the frame with highest confidence
            best_frame, confidence = max(motion_frames, key=lambda x: x[1])
            
            # Create a snapshot
            pil_img = Image.fromarray(cv2.cvtColor(best_frame, cv2.COLOR_BGR2RGB) if len(best_frame.shape) == 3 else best_frame)
            buffer = BytesIO()
            pil_img.save(buffer, format="JPEG")
            buffer.seek(0)
            
            # Create the motion event
            event = MotionEvent(
                camera=camera,
                timestamp=timezone.now(),
                confidence=confidence
            )
            
            # Save the snapshot
            event.snapshot.save(
                f"motion_{camera_id}_{int(time.time())}.jpg",
                ContentFile(buffer.read())
            )
            
            event.save()
            logger.info(f"Saved motion event for camera {camera_id}")
            
            return event
            
        except Exception as e:
            logger.error(f"Error saving motion event: {str(e)}")
            return None

# Singleton instance
camera_service = CameraService()
