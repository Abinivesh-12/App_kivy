import cv2
import numpy as np
from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock

class CameraFrameOverlay(Widget):
    def __init__(self, camera, **kwargs):
        super(CameraFrameOverlay, self).__init__(**kwargs)
        self.camera = camera

        self.bind(size=self.update_frame_position)

        frame_width = -400
        frame_height = -400

        # Create red rectangular borders initially
        with self.canvas:
            self.border_color = Color(1, 0, 0)  # Red color for the borders
            self.border_top = Line(points=[0, frame_height, frame_width, frame_height], width=2)
            self.border_bottom = Line(points=[0, 0, frame_width, 0], width=2)
            self.border_left = Line(points=[0, 0, 0, frame_height], width=2)
            self.border_right = Line(points=[frame_width, 0, frame_width, frame_height], width=2)

        # Calculate the initial frame position to be centered
        self.update_frame_position()

    def update_frame(self, color):
        self.border_color.rgba = color

    def update_frame_position(self, *args):
        # Calculate the frame position to be centered
        center_x = (self.width - self.border_right.points[2]) / 2
        center_y = (self.height - self.border_top.points[0]) / 2
        frame_width = 400
        frame_height = 200

        # Update the frame position
        self.border_top.points = [center_x, center_y + frame_height, center_x + frame_width, center_y + frame_height]
        self.border_bottom.points = [center_x, center_y, center_x + frame_width, center_y]
        self.border_left.points = [center_x, center_y, center_x, center_y + frame_height]
        self.border_right.points = [center_x + frame_width, center_y, center_x + frame_width, center_y + frame_height]

class CameraApp(App):
    def build(self):
        self.layout = RelativeLayout()

        self.camera = Camera(resolution=(640, 480), play=True)
        self.layout.add_widget(self.camera)

        self.result_label = Label(text="Pupil Diameter: -\nIris Diameter: -", size_hint=(None, None), size=(300, 60), pos_hint={'x': 0.7, 'y': 0.1})
        self.layout.add_widget(self.result_label)

        self.capture_button = Button(text="Capture Image", size_hint=(None, None), size=(150, 50), pos_hint={'x': 0.7, 'y': 0.0})
        self.capture_button.bind(on_press=self.capture_image)
        self.layout.add_widget(self.capture_button)

        self.retake_button = Button(text="Retake", size_hint=(None, None), size=(150, 50), pos_hint={'x': 0.1, 'y': 0.0})
        self.retake_button.bind(on_press=self.retake_image)
        self.layout.add_widget(self.retake_button)

        self.camera_frame_overlay = CameraFrameOverlay(self.camera)
        self.layout.add_widget(self.camera_frame_overlay)

        self.process_frame = True  # Flag to control frame processing

        # Periodically check for an eye inside the rectangular area
        Clock.schedule_interval(self.check_for_eye, 1.0 / 5.0)  # 5 times per second
        self.capture_button.disabled = False
        self.retake_button.disabled = True
        return self.layout

    def check_for_eye(self, dt):
        if not self.process_frame:
            return

        # Capture a single frame from the camera
        texture = self.camera.texture
        frame = np.frombuffer(texture.pixels, dtype='uint8')
        frame = frame.reshape(texture.height, texture.width, 4)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

        # Pupil and iris detection
        pupil_diameter, iris_diameter = detect_pupil_iris(frame)

        # Display the result
        self.result_label.text = f"Pupil Diameter: {pupil_diameter:.2f} pixels\nIris Diameter: {iris_diameter:.2f} pixels"

        # Change the border color based on eye detection
        if pupil_diameter > 0:
            self.camera_frame_overlay.update_frame((0, 1, 0, 1))  # Green color for the borders
        else:
            self.camera_frame_overlay.update_frame((1, 0, 0, 1))  # Red color for the borders

    def capture_image(self, instance):
        self.process_frame = False  # Stop processing frames
        self.capture_button.disabled = True
        self.retake_button.disabled = False
        # Implement your image capture logic here

    def retake_image(self, instance):
        self.process_frame = True  # Start processing frames
        self.capture_button.disabled = False
        self.retake_button.disabled = True

# Replace this with your actual pupil and iris detection logic
def detect_pupil_iris(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    rows = gray.shape[0]

    # Hough Transform for pupil detection
    circles_pupil = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=rows/8,
                                    param1=100, param2=23,
                                    minRadius=0, maxRadius=40)

    # Hough Transform for iris detection
    circles_iris = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=rows/8,
                                   param1=100, param2=50,
                                   minRadius=50, maxRadius=200)  # Adjust these values

    pupil_diameter = iris_diameter = 0

    if circles_pupil is not None:
        circles_pupil = np.uint16(np.around(circles_pupil))
        pupil_diameter = circles_pupil[0, 0, 2] * 2

    if circles_iris is not None:
        circles_iris = np.uint16(np.around(circles_iris))
        iris_diameter = circles_iris[0, 0, 2] * 2

    return pupil_diameter, iris_diameter

if __name__ == '__main__':
    CameraApp().run()