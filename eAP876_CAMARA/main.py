import cv2
import numpy as np

def simple_depth_decode(depth_frame):
    """Simple and fast depth decoding"""
    if len(depth_frame.shape) == 3:
        # Try green channel first (often contains depth info)
        depth_data = depth_frame[:, :, 1]
    else:
        depth_data = depth_frame
    
    # Simple noise reduction
    depth_filtered = cv2.medianBlur(depth_data, 3)
    
    return depth_filtered

# Initialize cameras
rgb_cap = cv2.VideoCapture(0)
depth_cap = cv2.VideoCapture(2)

if not rgb_cap.isOpened():
    print("Cannot open RGB camera")
    exit()

if not depth_cap.isOpened():
    print("Cannot open depth camera")
    exit()

# Set lower resolution for better performance
rgb_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
rgb_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
depth_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
depth_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# Set frame rate
rgb_cap.set(cv2.CAP_PROP_FPS, 15)
depth_cap.set(cv2.CAP_PROP_FPS, 15)

print("Starting lightweight camera display...")
print("Press 'q' to quit")
print("Press '1' for RGB only")
print("Press '2' for Depth only")
print("Press '3' for Both")

display_mode = 3

while True:
    ret_rgb, rgb_frame = rgb_cap.read()
    ret_depth, depth_frame = depth_cap.read()
    
    if not ret_rgb or not ret_depth:
        print("Failed to read frames")
        break
    
    # Simple depth processing
    depth_processed = simple_depth_decode(depth_frame)
    
    # Display based on mode
    if display_mode == 1:  # RGB only
        cv2.imshow('RGB Camera', rgb_frame)
    
    elif display_mode == 2:  # Depth only
        cv2.imshow('Depth Camera', depth_processed)
        
    elif display_mode == 3:  # Both
        # Resize to same height for side-by-side display
        h = min(rgb_frame.shape[0], depth_processed.shape[0])
        rgb_resized = cv2.resize(rgb_frame, (320, h))
        depth_resized = cv2.resize(depth_processed, (320, h))
        
        # Convert depth to color for display
        depth_color = cv2.applyColorMap(depth_resized, cv2.COLORMAP_JET)
        
        # Side by side display
        combined = np.hstack([rgb_resized, depth_color])
        cv2.imshow('RGB + Depth', combined)
    
    # Handle key presses
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('1'):
        display_mode = 1
        cv2.destroyAllWindows()
        print("Switched to RGB only")
    elif key == ord('2'):
        display_mode = 2
        cv2.destroyAllWindows()
        print("Switched to Depth only")
    elif key == ord('3'):
        display_mode = 3
        cv2.destroyAllWindows()
        print("Switched to Both cameras")

rgb_cap.release()
depth_cap.release()
cv2.destroyAllWindows()