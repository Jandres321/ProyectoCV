import cv2
import numpy as np
import os
import time


# Posibles patrones: "CIRCULO", "PICO", "FLECHA", "CUADRADO", "MONTANA"
EXPECTED_SEQUENCE = ["MONTANA"]
WIDTH = 1280
HEIGHT = 720
ROI_SIZE = 450          
COUNTDOWN_SECONDS = 5   

MIN_MOVEMENT = 700

RED_COLOR = (0, 0, 255)
GREEN_COLOR = (0, 255, 0)
BLUE_COLOR = (255, 0, 0)
YELLOW_COLOR = (0, 255, 255)
ROI_COLOR = (200, 200, 200)

def compute_contours(img_gray):
    blurred_img = cv2.GaussianBlur(img_gray, (5, 5), 0)  # Suavizado gausiano
    img_thres = cv2.adaptiveThreshold(blurred_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    img_morph = cv2.morphologyEx(img_thres, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))  # Apertura morfológica
    contours, hierchary = cv2.findContours(img_morph, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_SIMPLE)
    return contours, hierchary

def detect_pattern(contours, hierchary, img_shape):
    max_area = 0
    detected_pattern = None
    best_approx = None

    height, width = img_shape[:2]
    min_total_area = (height * width) * 0.02
    max_total_area = (height * width) * 0.8

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)

        if min_total_area < area < max_total_area:
            x, y, w, h = cv2.boundingRect(contour)

            if x < 2 or y < 2 or (x+w) > width-2 or (y+h) > height-2:
                continue

            perimeter = cv2.arcLength(contour, closed=True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, closed=True)
            num_vert = len(approx)
            is_convex = cv2.isContourConvex(approx)

            pattern_label = f"num_vert_{num_vert}"
            

            if num_vert > 7 and is_convex:
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    if circularity > 0.7:
                        pattern_label = "CIRCULO"

            elif num_vert == 4 and not is_convex:
                # Todo poligono de 4 vertices no convexo es una flecha
                pattern_label = "FLECHA"
            elif num_vert == 5 and not is_convex:
                try:
                    hull_points = cv2.convexHull(approx, returnPoints=False)
                    defects = cv2.convexityDefects(approx, hull_points)

                except cv2.error as e:
                    defects = None

                defect_count = 0
                if defects is not None:
                    for j in range(defects.shape[0]):
                        _, _, _, d = defects[j, 0]
                        if d > (max(w, h) * 20):
                            defect_count += 1
                if defect_count == 1:
                    pattern_label = "MONTANA"
                elif defect_count == 2:
                    pattern_label = "PICO"

            elif num_vert == 4 and is_convex:
                pattern_label = "CUADRADO"
            
            if pattern_label and area > max_area:
                max_area = area
                detected_pattern = pattern_label
                best_approx = approx
        
    return detected_pattern, best_approx
        
    
class AutoKalmanTracker:
    def __init__(self):
        self.kalman = cv2.KalmanFilter(4, 2)
        self.kalman.measurementMatrix = np.array([[1,0,0,0],[0,1,0,0]], np.float32)
        self.kalman.transitionMatrix = np.array([[1,0,1,0],[0,1,0,1],[0,0,1,0],[0,0,0,1]], np.float32)
        self.kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=25, detectShadows=False)
        self.first_detection = True
        self.initial_pos = None

        self.best_w = 100
        self.best_h = 100

    def update(self, frame):
        mask = self.bg_subtractor.apply(frame)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        measurement = None
        if contours:
            max_c = max(contours, key=cv2.contourArea)
            if cv2.contourArea(max_c) > 3000:
                x,y,w,h = cv2.boundingRect(max_c)

                self.best_w = w
                self.best_h = h
                measurement = np.array([[np.float32(x+w/2)], [np.float32(y+h/2)]])

        prediction = self.kalman.predict()
        if measurement is not None:
            if self.first_detection:
                self.kalman.statePre = np.array([[measurement[0,0]], [measurement[1,0]], [0], [0]], dtype=np.float32)
                self.kalman.statePost = np.array([[measurement[0,0]], [measurement[1,0]], [0], [0]], dtype=np.float32)
                self.initial_pos = (measurement[0,0], measurement[1,0])
                self.first_detection = False
            estimated = self.kalman.correct(measurement)
        else:
            estimated = prediction
        return (int(estimated[0]), int(estimated[1]), self.best_w, self.best_h), not self.first_detection


def main(video_source, width=1280, height=720, mtx=None, dist=None):

    cap = cv2.VideoCapture(video_source, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print(f"No se pudo conectar a: {video_source}")
        return

    window_name = "Despertador"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    ret, first_frame = cap.read()
    if not ret:
        print("No se pudo leer el primer frame.")
        return
        
    h_orig, w_orig = first_frame.shape[:2]
    mapx, mapy = None, None
    roi_crop = None

    if mtx is not None:
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w_orig,h_orig), 1, (w_orig,h_orig))
        mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (w_orig,h_orig), 5)
        roi_crop = roi

    detected_sequence = []
    last_detection_time = time.time()
    state = "BLOQUEADO" 
    
    reset_message = False
    countdown_start_time = 0
    color = RED_COLOR
    
    roi_x = (width - ROI_SIZE) // 2
    roi_y = (height - ROI_SIZE) // 2

    try:
        t0 = time.time()
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Frame perdido (buffering...)")
                continue
            
            if mapx is not None and mapy is not None:
                frame_undistorted = cv2.remap(frame, mapx, mapy, cv2.INTER_LINEAR)
                
                x, y, w_roi, h_roi = roi_crop
                frame_undistorted = frame_undistorted[y:y+h_roi, x:x+w_roi]
            else:
                frame_undistorted = frame

            frame_display = cv2.resize(frame_undistorted, (width, height))
            gray = cv2.cvtColor(frame_display, cv2.COLOR_BGR2GRAY)


            if state == "BLOQUEADO":
                cv2.rectangle(frame_display, (roi_x, roi_y), (roi_x + ROI_SIZE, roi_y + ROI_SIZE), ROI_COLOR, 2)
                gray_roi = gray[roi_y:roi_y+ROI_SIZE, roi_x:roi_x+ROI_SIZE]
                
                contours, hierchary = compute_contours(gray_roi)
                pattern, approx = detect_pattern(contours, hierchary, gray_roi.shape)

                if pattern:
                    expected_shape = EXPECTED_SEQUENCE[len(detected_sequence)]
                    t = time.time()
                    is_correct = (pattern == expected_shape)


                    if is_correct:
                        color = GREEN_COLOR
                    elif not is_correct and (t - last_detection_time) > 2.0:
                        color = RED_COLOR

                    approx_global = approx + [roi_x, roi_y]

                    if pattern == "CIRCULO":
                        (x_circle, y_circle), radius = cv2.minEnclosingCircle(approx_global)
                        center = (int(x_circle), int(y_circle))
                        radius = int(radius)
                        cv2.circle(frame_display, center, radius, color, 3)
                    else:
                        cv2.drawContours(frame_display, [approx_global], -1, color, 3)
                    
                    

                    cv2.putText(frame_display, pattern, (10, height - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

                    
                    if is_correct and (t - last_detection_time) > 0.2:  
                        detected_sequence.append(pattern)
                        last_detection_time = t
                        reset_message = False

                    elif not is_correct and (t - last_detection_time) > 2.0:  # Dar tiempo para cambiar de forma
                        detected_sequence = []
                        reset_message = True
                        last_detection_time = t

                if reset_message:
                    cv2.putText(frame_display, "SECUENCIA REINICIADA", (10, height - 80), cv2.FONT_HERSHEY_SIMPLEX, 1, RED_COLOR, 2)

                if detected_sequence == EXPECTED_SEQUENCE:
                    state = "COUNTDOWN"
                    countdown_start_time = time.time()
                    reset_message = False
            
            elif state == "COUNTDOWN":
                elapsed = time.time() - countdown_start_time
                remaining = int(COUNTDOWN_SECONDS - elapsed) + 1
                
                text = str(remaining)
                font_scale = 10
                thickness = 10
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
                text_x = (width - text_size[0]) // 2
                text_y = (height + text_size[1]) // 2
                
                cv2.putText(frame_display, "Iniciando tracking...", (text_x - 250, text_y + 100), cv2.FONT_HERSHEY_SIMPLEX, 2, YELLOW_COLOR, 3)
                cv2.putText(frame_display, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, YELLOW_COLOR, thickness)

                if remaining <= 0:
                    state = "TRACKING"
                    tracker = AutoKalmanTracker()

            elif state == "TRACKING":
                (kx, ky, w, h), active = tracker.update(frame_display)
                cv2.putText(frame_display, "LEVANTATE DE LA CAMA", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, BLUE_COLOR, 2)
                
                if active and tracker.initial_pos:
                    cv2.drawMarker(frame_display, (kx, ky), GREEN_COLOR, cv2.MARKER_CROSS, 20, 2)

                    top_left = (kx - w//2, ky - h//2)
                    bottom_right = (kx + w//2, ky + h//2)
                    cv2.rectangle(frame_display, top_left, bottom_right, GREEN_COLOR, 2)

                    ix, iy = tracker.initial_pos
                    distancia = np.sqrt((kx-ix)**2 + (ky-iy)**2)
                    progreso = min(distancia/MIN_MOVEMENT, 1.0)
                    
                    cv2.rectangle(frame_display, (50,100), (350,130), (50,50,50), -1)
                    cv2.rectangle(frame_display, (50,100), (50+int(300*progreso),130), GREEN_COLOR, -1)

                    if distancia > MIN_MOVEMENT:
                        state = "UNLOCKED"
                        shutdown_start_time = time.time()

            elif state == "UNLOCKED":
                cv2.putText(frame_display, "DESPERTADOR DESACTIVADO", (10, height - 80), cv2.FONT_HERSHEY_SIMPLEX, 1, BLUE_COLOR, 2)

                
                elapsed = time.time() - shutdown_start_time
                remaining = int(COUNTDOWN_SECONDS - elapsed) + 1
                
                text = str(remaining)
                font_scale = 10
                thickness = 10
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
                text_x = (width - text_size[0]) // 2
                text_y = (height + text_size[1]) // 2
                
                cv2.putText(frame_display, "Saliendo del sistema", (text_x - 150, text_y - 250), cv2.FONT_HERSHEY_SIMPLEX, 2, YELLOW_COLOR, 3)
                cv2.putText(frame_display, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, YELLOW_COLOR, thickness)

                if remaining <= 0:
                    break
            
            # FPS
            t1 = time.time()
            fps = 1 / (t1 - t0) if (t1-t0) > 0 else 0
            t0 = t1
            cv2.putText(frame_display, f"FPS: {fps:.2f}", (width - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            cv2.imshow(window_name, frame_display)

            if (cv2.waitKey(1) & 0xFF) == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    url_camara = "http://192.168.0.12:8080/video"

    calib_data = np.load('calibration_parameters.npz')
    mtx, dist = calib_data['intr'], calib_data['dist']

    main(video_source=url_camara, width=WIDTH, height=HEIGHT, mtx=mtx, dist=dist)