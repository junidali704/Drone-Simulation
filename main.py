import pyzipper
import sys
import cv2
import zipfile
import os
from PyQt5.QtWidgets import QApplication, QOpenGLWidget, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QPainter, QPixmap, QColor
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import time
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QInputDialog,QLineEdit,QMessageBox
from PyQt5.QtCore import QPropertyAnimation, QRect
import numpy as np
from database import create_connection
from cryptography.fernet import Fernet
from math import sqrt
import subprocess
fernet_key = Fernet.generate_key()
fernet = Fernet(fernet_key)

class GLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        self.angle = 0
        self.x_offset = 0
        self.y_offset = 0
        self.move_direction = None
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.moveDrone)
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self.updateRotation)
        self.rotation_timer.start(16)  
        self.logo = QPixmap("pc.png")  
        self.line_start = (0, 0, 0)  
        self.line_end = (0, 0, -10)  
        self.line_color = (1.0, 0.0, 0.0)  

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h, 1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -10)
        self.widget_width = w
        self.widget_height = h

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Draw the drone with its transformations
        glTranslatef(self.x_offset, self.y_offset, -10)
        glRotatef(self.angle, 0, 1, 0)
        self.drawDrone()

        # Reset transformation matrix to draw the line in world coordinates
        glLoadIdentity()

        # Draw the line from pc.png to drone
        self.drawLineFromPCToDrone()

        # Draw the image (pc.png)
        self.drawImage()


        

    def updateRotation(self):
        self.angle += 1.0
        if self.angle >= 360:
            self.angle -= 360
        self.update()

    def drawCylinder(self, radius, height, slices):
        for i in range(slices):
            angle = 2 * math.pi * i / slices
            next_angle = 2 * math.pi * (i + 1) / slices
            glBegin(GL_QUADS)
            glVertex3f(radius * math.cos(angle), 0, radius * math.sin(angle))
            glVertex3f(radius * math.cos(next_angle), 0, radius * math.sin(next_angle))
            glVertex3f(radius * math.cos(next_angle), height, radius * math.sin(next_angle))
            glVertex3f(radius * math.cos(angle), height, radius * math.sin(angle))
            glEnd()

    def drawBox(self, width, height, depth):
        glBegin(GL_QUADS)
        glVertex3f(-width / 2, -height / 2, depth / 2)
        glVertex3f(width / 2, -height / 2, depth / 2)
        glVertex3f(width / 2, height / 2, depth / 2)
        glVertex3f(-width / 2, height / 2, depth / 2)
        
        glVertex3f(-width / 2, -height / 2, -depth / 2)
        glVertex3f(-width / 2, height / 2, -depth / 2)
        glVertex3f(width / 2, height / 2, -depth / 2)
        glVertex3f(width / 2, -height / 2, -depth / 2)
        
        glVertex3f(-width / 2, height / 2, -depth / 2)
        glVertex3f(-width / 2, height / 2, depth / 2)
        glVertex3f(width / 2, height / 2, depth / 2)
        glVertex3f(width / 2, height / 2, -depth / 2)
        
        glVertex3f(-width / 2, -height / 2, -depth / 2)
        glVertex3f(width / 2, -height / 2, -depth / 2)
        glVertex3f(width / 2, -height / 2, depth / 2)
        glVertex3f(-width / 2, -height /2, depth / 2)
        
        glVertex3f(width / 2, -height / 2, -depth / 2)
        glVertex3f(width / 2, height / 2, -depth / 2)
        glVertex3f(width / 2, height / 2, depth / 2)
        glVertex3f(width / 2, -height / 2, depth / 2)
        
        glVertex3f(-width / 2, -height / 2, -depth / 2)
        glVertex3f(-width / 2, -height / 2, depth / 2)
        glVertex3f(-width / 2, height / 2, depth / 2)
        glVertex3f(-width / 2, height / 2, -depth / 2)
        
        glEnd()

    def drawDrone(self):
        glColor3f(0.0, 0.0, 1.0)
        self.drawBox(1, 0.25, 1)
        
        glColor3f(1.0, 0.0, 0.0)
        self.drawBox(2.5, 0.1, 0.1)
        glPushMatrix()
        glRotatef(90, 0, 1, 0)
        self.drawBox(2.5, 0.1, 0.1)
        glPopMatrix()

        glColor3f(0.0, 1.0, 0.0)
        positions = [(1.25, 0, 1.25), (-1.25, 0, 1.25), (1.25, 0, -1.25), (-1.25, 0, -1.25)]
        for (x, y, z) in positions:
            glPushMatrix()
            glTranslatef(x, y, z)
            self.drawCylinder(0.1, 0.05, 16)
            glPopMatrix()

    def drawImage(self):
        image = self.logo.toImage().mirrored(False, True)  
        width = image.width()
        height = image.height()
        
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.widget_width, self.widget_height, 0, -1, 1)  
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glRasterPos2i(self.widget_width - width, self.widget_height - height)  
        glDrawPixels(width, height, GL_RGBA, GL_UNSIGNED_BYTE, image.bits().asstring(width * height * 4))
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
    
    
    def moveRight(self):
        if self.x_offset < self.width() / 200:
            self.x_offset += 0.1
        self.update()

    def moveLeft(self):
        if self.x_offset > -self.width() / 200:
            self.x_offset -= 0.1
        self.update()

    def moveUp(self):
        if self.y_offset < self.height() / 200:
            self.y_offset += 0.1
        self.update()

    def moveDown(self):
        if self.y_offset > -self.height() / 200:
            self.y_offset -= 0.1
        self.update()

    def moveDrone(self):
        if self.move_direction == 'left':
            self.moveLeft()
        elif self.move_direction == 'right':
            self.moveRight()
        elif self.move_direction == 'up':
            self.moveUp()
        elif self.move_direction == 'down':
            self.moveDown()
    
    def get_drone_position(self):
        return self.x_offset, self.y_offset, -10

    def get_pc_position(self):
        return (self.width() - self.logo.width()) / 2, self.height() - self.logo.height() - 10, 0
    def drawLineFromPCToDrone(self):
        # Get positions of pc.png and drone
        pc_x, pc_y, pc_z = self.get_pc_position()
        drone_x, drone_y, drone_z = self.get_drone_position()

        # Calculate the distance between the drone and PC
        distance = math.sqrt((pc_x - drone_x)**2 + (pc_y - drone_y)**2)

        # If the distance is less than or equal to 10 (arbitrary value), stop updating the line
        if distance <= 10:
            return

        # Calculate the rotation angle
        angle = 248  # Replace with your actual calculation

        # If the angle is less than 0, change the direction of the line
        if angle < 0:
            angle = -angle  # Take the absolute value
            direction = -1  # Change the direction
        else:
            direction = 1  # Keep the original direction

        # Translate the line to the drone's position
        glTranslatef(drone_x, drone_y, drone_z)

        # Rotate the line by the calculated angle around the drone's position
        glRotatef(angle, direction, 0, 0)  # Rotate the line by the calculated angle

        # Draw the line from pc.png to drone
        glBegin(GL_LINES)
        glColor3f(1.0, 1.0, 1.0)  # White color for the line
        glVertex3f(pc_x, pc_y, pc_z)
        glVertex3f(0, 0, 0)
        glEnd()

        # Reset the transformation matrix
        glLoadIdentity()

from drone import encrypt_message

from drone import store_encrypted_message_in_db
class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Drone Simulation')
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()
        self.gl_widget = GLWidget(self)
        layout.addWidget(self.gl_widget)
        self.setLayout(layout)
        

        
        self.capture_button = QPushButton("Capture", self)
        layout.addWidget(self.capture_button)
        self.capture_button.clicked.connect(self.capture_and_store_image)

                # Button to Run drone.py
        self.main_button = QPushButton("Home", self)
        layout.addWidget(self.main_button)
        self.main_button.clicked.connect(self.handle_main_layout)

        
        self.circle = ClickableCircle(self)
        self.circle.setGeometry((self.width() - 50) // 2, self.height() - 70, 50, 50)  
        self.circle.directionChanged.connect(self.startMoving)
        self.circle.directionStopped.connect(self.stopMoving)

        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.updateCirclePosition)
        
        self.drone_thread = DroneThread(self)
        self.drone_thread.start()
        self.drone_thread.drone_position_changed.connect(self.update_box_position)

        self.fernet = Fernet(Fernet.generate_key())
        

        self.box_move_timer = QTimer(self)
        self.box_move_timer.setSingleShot(True)
        self.box_move_timer.timeout.connect(self.move_box_to_pc_position)
        
        
        self.box = QLabel(self)
        self.box.setFixedSize(20, 20)
        self.box.setStyleSheet("background-color: red;")
        self.box.hide()
    
    def handle_main_layout(self):
        try:
            # Run drone.py using subprocess
            subprocess.run(["python", "drone.py"], check=True)
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "drone.py file not found!")
        
    def update_box_position(self, drone_x, drone_y, drone_z):
        # Convert drone position from OpenGL coordinates to widget coordinates
        drone_screen_pos = self.gl_widget.mapToGlobal(QPoint(int(drone_x), int(drone_y)))

        # Calculate new position for the box (just below the drone)
        new_x = drone_screen_pos.x()
        new_y = drone_screen_pos.y() + 50  # Adjust the value '50' to position the box just below the drone

        # Move the box to the new position

        
    def move_box_to_pc_position(self):
        # Get the position of pc.png
        pc_x, pc_y, _ = self.gl_widget.get_pc_position()

        # Calculate the target position for the box (left bottom corner where pc.png is)
        target_x = pc_x
        target_y = pc_y + self.gl_widget.logo.height()

        # Move the box to the target position
        self.box.move(int(pc_x), int(pc_y))
        self.box.show()

    
    def save_image(self, image):
        # Get the filename for the zip file
        zip_filename, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "Zip Files (*.zip)")

        # Check if the user canceled the dialog
        if not zip_filename:
            return

        # Get the password from the user
        password, ok = QInputDialog.getText(self, "Enter Password", "Enter the password:", QLineEdit.Password)

        # Check if the user canceled the input dialog or did not enter a password
        if not ok or not password:
            return

        # Convert the image to bytes
        _, image_bytes = cv2.imencode('.png', image)

        # Open the zip file with pyzipper
        with pyzipper.AESZipFile(zip_filename, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zipf:
            # Set the password for the zip file
            zipf.pwd = password.encode()
            # Generate a unique filename
            filename = "captured_image.png"
            # Write the image bytes to the zip file
            zipf.writestr(filename, image_bytes.tobytes())

        print(f"Image saved to {zip_filename} as {filename} with password")

    def open_image_from_zip(self):
        # Get the zip filename from the user
        zip_filename, _ = QFileDialog.getOpenFileName(self, "Open Zip File", "", "Zip Files (*.zip)")

        # Check if the user canceled the dialog
        if not zip_filename:
            return

        # Get the password from the user
        password, ok = QInputDialog.getText(self, "Enter Password", "Enter the password:", QLineEdit.Password)

        # Check if the user canceled the input dialog or did not enter a password
        if not ok or not password:
            return

        # Try to open the zip file with the provided password
        try:
            with pyzipper.AESZipFile(zip_filename, 'r') as zipf:
                zipf.pwd = password.encode()
                # Extract the contents of the zip file
                file_list = zipf.namelist()
                if file_list:  # Check if the zip file is not empty
                    # Assuming there is only one image file in the zip
                    image_data = zipf.read(file_list[0])
                    # Process the image data as needed (e.g., display it in an image viewer)
                    # You can also save it to a temporary file and open it using an external program
                    # For demonstration, let's assume displaying the image using OpenCV
                    image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
                    cv2.imshow("Captured Image", image)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                else:
                    QMessageBox.warning(self, "Error", "No files found in the zip archive.")
        except (pyzipper.BadZipFile, RuntimeError):
            QMessageBox.warning(self, "Error", "Invalid zip file or incorrect password.")

    def capture_and_store_image(self):
        # Ensure both x and y offsets are integers
        x_pos = int(self.gl_widget.x_offset + self.gl_widget.width() // 2 - self.box.width() // 2)
        y_pos = int(self.gl_widget.y_offset + self.gl_widget.height() // 2 + 10)

        self.box.move(x_pos, y_pos)
        self.box.show()

        end_x = self.width() - self.gl_widget.logo.width()
        end_y = self.height() - self.gl_widget.logo.height() - 50  # Move it 50 pixels higher

        self.animation = QPropertyAnimation(self.box, b"geometry")
        self.animation.setDuration(2000)
        self.animation.setStartValue(self.box.geometry())
        self.animation.setEndValue(QRect(end_x, end_y, self.box.width(), self.box.height()))
        self.animation.finished.connect(self.hideBox)  # Connect finished signal to hideBox slot
        self.animation.start()

        drone_position = self.gl_widget.mapFromGlobal(self.gl_widget.mapToGlobal(QPoint(0, 0)))

        end_x = self.width() - self.gl_widget.logo.width()
        end_y = self.height() - self.gl_widget.logo.height()

        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()

        if ret:
            encrypted_data = self.encrypt_image(frame)
            self.store_image_in_db(encrypted_data)
            print("Image captured and stored in database")

            drone_x, drone_y, drone_z = self.gl_widget.get_drone_position()
            pc_x, pc_y, pc_z = self.gl_widget.get_pc_position()

            dx = pc_x - drone_x
            dy = pc_y - drone_y
            distance = math.sqrt(dx**2 + dy**2)

            # Save the image locally
            self.save_image(frame)

            print(f"Security Level After Encryption: {self.initial_security_level}")
        message, ok1 = QInputDialog.getText(self, "Enter Message", "Enter the message:")
        passwordk, ok2 = QInputDialog.getText(self, "Enter Password", "Enter the Key:")

        if ok1 and message and ok2 and passwordk:
            self.store_message(message, passwordk)
        else:
            print("Failed to capture image or missing message/password")

 
    
    def hideBox(self):
        self.box.hide()
    
    
    def encrypt_image(self, image):
        _, image_binary = cv2.imencode('.jpg', image)
        encrypted_data = self.fernet.encrypt(image_binary.tobytes())
        return encrypted_data

    def store_image_in_db(self, encrypted_data):
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO encrypted_images (encrypted_image) VALUES (?)", (encrypted_data,))
        connection.commit()
        connection.close()
    def access_security_level(self):
        # Example function to access security level and print result
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT security_level FROM security_table WHERE id = ?", (1,))
        result = cursor.fetchone()
        if result:
            security_level = result[0]
            print(f"Security Level: {security_level}")
        connection.close()
    
    


    # Function to calculate security level based on encryption parameters
    def calculate_security_level(encryption_method, key_length):
        # Example mapping of encryption parameters to security levels
        if encryption_method == "AES" and key_length >= 256:
            return "High Security"
        elif encryption_method == "AES" and key_length >= 128:
            return "Medium Security"
        else:
            return "Low Security"
    def store_message(self, message, passwordk):
        encrypted_message = encrypt_message(message)
        encrypted_passwordk = encrypt_message(passwordk)
        
        # Call the function to store both encrypted message and passwordk
        store_encrypted_message_in_db(encrypted_message, encrypted_passwordk)
        print("Message and password stored in database")
    # Simulated encryption function
    def encrypt_data(data, encryption_method, key_length):
        # Perform encryption (this is a placeholder)
        # In real scenario, use proper encryption library (e.g., cryptography module)
        encrypted_data = f"Encrypted: {data}"
        return encrypted_data

    # Example scenario
    encryption_method = "AES"
    key_length = 256
    data_to_encrypt = "Sensitive data"

    # Calculate security level before encryption
    initial_security_level = calculate_security_level(encryption_method, key_length)
    
    # Perform encryption
    encrypted_data = encrypt_data(data_to_encrypt, encryption_method, key_length)

    # Calculate security level after encryption
    actual_encryption_strength = math.ceil(math.log2(key_length))  # Example calculation
    final_security_level = calculate_security_level(encryption_method, actual_encryption_strength)

    # Display results
    print(f"Security Level Before Encryption: {final_security_level}")
    print(f"Encrypted Data: {encrypted_data}")
    

    def print_security_level(self):
        encryption_method = "AES"
        key_length = 256
        security_level = self.calculate_security_level(encryption_method, key_length)
        print("Security Level:", security_level)
    def resizeEvent(self, event):
        self.resize_timer.start(100)

    def updateCirclePosition(self):
        self.circle.setGeometry((self.width() - 50) // 2, self.height() - 120, 50, 50)

    def startMoving(self, direction):
        self.gl_widget.move_direction = direction
        if not self.gl_widget.move_timer.isActive():
            self.gl_widget.move_timer.start(16)
    def stopMoving(self):
        self.gl_widget.move_timer.stop()
    

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Use painter to draw on self
        painter.fillRect(self.rect(), QColor('lightgray'))
        painter.drawText(self.rect(), Qt.AlignCenter, "Hello, QPainter!")
        painter.end()  # Always end QPainter when done


class ClickableCircle(QWidget):
    directionChanged = pyqtSignal(str)
    directionStopped = pyqtSignal()

    def __init__(self, parent=None):
        super(ClickableCircle, self).__init__(parent)
        self.setFixedSize(50, 50)
        self.direction = None
        self.pressed = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(Qt.red)
        painter.drawEllipse(0, 0, self.width(), self.height())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressed = True
            self.direction = self.getDirection(event.pos())
            self.directionChanged.emit(self.direction)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressed = False
            self.directionStopped.emit()

    def mouseMoveEvent(self, event):
        if self.pressed:
            self.direction = self.getDirection(event.pos())
            self.directionChanged.emit(self.direction)

    def getDirection(self, pos):
        center = self.rect().center()
        dx = pos.x() - center.x()
        dy = pos.y() - center.y()

        if abs(dx) > abs(dy):
            if dx > 0:
                return 'right'
            else:
                return 'left'
        else:
            if dy > 0:
                return 'down'
            else:
                return 'up'

class DroneThread(QThread):
    drone_position_changed = pyqtSignal(float, float, float)  # Define the signal

    image_captured = pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drone = Drone()  
        self.fernet = Fernet(Fernet.generate_key())
    def run(self):
        while True:
            # Assuming capture_image returns the position as well
            image, drone_x, drone_y, drone_z = self.drone.capture_image()
            if image is not None:
                encrypted_data = self.encrypt_image(image)
                self.store_image_in_db(encrypted_data)
                self.image_captured.emit(image)
                # Emit the drone position signal
                self.drone_position_changed.emit(drone_x, drone_y, drone_z)
            time.sleep(5)  

    def encrypt_image(self, image):
        # Convert the image to a binary format
        ret, image_binary = cv2.imencode('.jpg', image)
        if ret:
            # Make sure image_binary is a bytes object
            image_binary = bytes(image_binary)
            # Encrypt the binary data
            encrypted_data = fernet.encrypt(image_binary)
            return encrypted_data
        else:
            print("Failed to encode image")
            return None

    def store_image_in_db(self, encrypted_data):
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO encrypted_images (encrypted_image) VALUES (?)", (encrypted_data,))
        connection.commit()
        connection.close()
class Drone:
    def capture_image(self):
        # Capture an image using OpenCV
        cap = cv2.VideoCapture(0)
        ret, image = cap.read()
        cap.release()

        # Assuming you have the drone position (X, Y, Z coordinates) already calculated
        drone_x, drone_y, drone_z = 0, 0, 0  # Replace with your actual drone position
        
        # Return the captured image along with the drone position
        return image, drone_x, drone_y, drone_z

class QLabel(QLabel):
    def animate_move(self, start_x, start_y, end_x, end_y, duration):
        start_x = int(start_x)
        start_y = int(start_y)
        end_x = int(end_x)
        end_y = int(end_y)
        
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(duration)
        self.animation.setStartValue(QRect(start_x, start_y, self.width(), self.height()))
        self.animation.setEndValue(QRect(end_x, end_y, self.width(), self.height()))
        self.animation.start()





        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800,600)
    window.show()
    sys.exit(app.exec_())
