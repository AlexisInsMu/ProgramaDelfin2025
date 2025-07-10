import cv2
import numpy as np

def get_red_mask(img):
    """Obtiene una máscara binaria para el color rojo en la imagen BGR."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # Rango bajo de rojo
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    # Rango alto de rojo
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    return mask

def find_largest_convex_region(mask):
    """Encuentra el contorno convexo más grande en la máscara."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest = None
    max_area = 0
    for cnt in contours:
        hull = cv2.convexHull(cnt)
        area = cv2.contourArea(hull)
        if area > max_area:
            max_area = area
            largest = hull
    return largest

def get_centroid(contour):
    """Calcula el centroide de un contorno."""
    M = cv2.moments(contour)
    if M["m00"] == 0:
        return None
    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    return (cx, cy)

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("No se pudo abrir la cámara")
        return
    cv2.namedWindow("Detección Ojo Rojo", cv2.WINDOW_NORMAL)
    cv2.namedWindow("Mascara Roja", cv2.WINDOW_NORMAL)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        mask = get_red_mask(frame)
        largest_hull = find_largest_convex_region(mask)
        output = frame.copy()

        if largest_hull is not None:
            centroid = get_centroid(largest_hull)
            cv2.drawContours(output, [largest_hull], -1, (0,255,0), 2)
            if centroid:
                cv2.circle(output, centroid, 5, (255,0,0), -1)
                cv2.putText(output, f"Centroide: {centroid}", (centroid[0]+10, centroid[1]), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)
        
        cv2.imshow("Detección Ojo Rojo", output)
        cv2.imshow("Mascara Roja", mask)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()