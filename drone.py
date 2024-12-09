import sys
import subprocess
import base64
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QMessageBox, QTableWidget, QTableWidgetItem, QDialog
from PyQt5.QtCore import Qt
from cryptography.fernet import Fernet
from database import create_connection
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QTableWidget, 
    QTableWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt

fernet_key = b'FudC2k1fLKwzs6fJCGsvCXSqfBBqTiD1cfgC92fFvps=' # Replace with your actual saved key
fernet = Fernet(fernet_key)
print(fernet_key)

def encrypt_message(message):
    """Encrypts the given message using Fernet encryption."""
    encrypted_message = fernet.encrypt(message.encode())
    return base64.b64encode(encrypted_message).decode()  # Store as base64 string

def store_encrypted_message_in_db(encrypted_message, encrypted_passwordk):
    """Stores the encrypted message and passwordk in the database."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (message, passwordk) VALUES (CONVERT(VARBINARY(MAX), ?), ?)",  # Convert encrypted_message to varbinary
        (encrypted_message, encrypted_passwordk)
    )
    conn.commit()
    cursor.close()
    conn.close()


def fetch_messages():
    """Fetches messages and their timestamps from the database."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT message, timestamp FROM messages")
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return messages



def decrypt_message(encrypted_message_base64):
    """Decrypts the base64 encoded message stored in the database."""
    try:
        # Decode the base64 message back to binary before decryption
        encrypted_message = base64.b64decode(encrypted_message_base64)
        decrypted_message = fernet.decrypt(encrypted_message).decode('utf-8')
        return decrypted_message
    except Exception as e:
        print(f"Error during decryption: {e}")
        return "Error decrypting message"

# def fetch_messages():
#     """Fetches decrypted messages and their timestamps from the database."""
#     conn = create_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT message, timestamp FROM messages")
#     messages = cursor.fetchall()
#     cursor.close()
#     conn.close()

    # Decrypt messages before returning
    decrypted_messages = []
    for message, timestamp in messages:
        decrypted_message = decrypt_message(message)
        decrypted_messages.append((decrypted_message, timestamp))
    
    return decrypted_messages

class MessageDialog(QDialog):
    def __init__(self, messages):
        super().__init__()

        # Dialog settings
        self.setWindowTitle("Stored Messages")
        self.setGeometry(100, 100, 800, 600)

        # Layout and table
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Encryption Input Field
        self.encrypt_label = QLabel("Enter message to encrypt:")
        self.encrypt_input = QTextEdit(self)
        self.encrypt_input.setPlaceholderText("Enter message here...")
        self.encrypt_input.setFixedHeight(50)  # Set fixed height for the field
        self.layout.addWidget(self.encrypt_label)
        self.layout.addWidget(self.encrypt_input)

        # Encrypt Button
        self.encrypt_button = QPushButton("Encrypt")
        self.encrypt_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 16px;
                color: #fff;
                background-color: #28a745;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.encrypt_button.clicked.connect(self.handle_encrypt)
        self.layout.addWidget(self.encrypt_button)

        # Decryption Input Field
        self.decrypt_label = QLabel("Enter encrypted message to decrypt:")
        self.decrypt_input = QTextEdit(self)
        self.decrypt_input.setPlaceholderText("Enter encrypted message here...")
        self.decrypt_input.setFixedHeight(50)  # Set fixed height for the field
        self.layout.addWidget(self.decrypt_label)
        self.layout.addWidget(self.decrypt_input)

        # Decrypt Button
        self.decrypt_button = QPushButton("Decrypt Message")
        self.decrypt_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 16px;
                color: #fff;
                background-color: #007bff;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.decrypt_button.clicked.connect(self.handle_decrypt)
        self.layout.addWidget(self.decrypt_button)

        # Encrypted Output Field
        self.encrypted_output_label = QLabel("Output:")
        self.encrypted_output = QTextEdit(self)
        self.encrypted_output.setPlaceholderText("Output will appear here...")
        self.encrypted_output.setReadOnly(True)  # Make this field read-only
        self.encrypted_output.setFixedHeight(50)  # Set fixed height for the field
        self.layout.addWidget(self.encrypted_output)

        # Table widget
        self.table_widget = QTableWidget()
        self.table_widget.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f2f2f2;
                padding: 10px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
            QTableWidgetItem {
                padding: 10px;
            }
            QTableWidget::item:selected {
                background-color: #e0e0e0;
            }
            QTableWidget::item {
                border-bottom: 1px solid #ddd;
            }
            QTableWidget::item:nth-child(even) {
                background-color: #f9f9f9;
            }
        """)
        self.layout.addWidget(self.table_widget)

        # Populate table
        self.populate_table(messages)

    def populate_table(self, messages):
        """Populates the table with messages and timestamps."""
        self.table_widget.setRowCount(len(messages))
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Message (Base64 Encoded)", "Timestamp"])

        for row, (message, timestamp) in enumerate(messages):
            # Assuming `message` is already base64-encoded
            message_item = QTableWidgetItem(message)  
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            timestamp_item = QTableWidgetItem(timestamp_str)

            # Set items in the table
            self.table_widget.setItem(row, 0, message_item)
            self.table_widget.setItem(row, 1, timestamp_item)

    def handle_encrypt(self):
        """Handle encryption of input message."""
        message = self.encrypt_input.toPlainText()
        if not message:
            QMessageBox.warning(self, "Warning", "Please enter a message to encrypt!")
            return

        # Encrypt the message
        encrypted_message = encrypt_message(message)

        # Display the encrypted message
        self.encrypted_output.setText(encrypted_message)

        QMessageBox.information(self, "Success", "Message encrypted successfully!")
        self.encrypt_input.clear()

    def handle_decrypt(self):
        """Handle decryption of the input message."""
        encrypted_message = self.decrypt_input.toPlainText()
        if not encrypted_message:
            QMessageBox.warning(self, "Warning", "Please enter an encrypted message to decrypt!")
            return

        # Decode the base64-encoded encrypted message and decrypt it
        decrypted_message = decrypt_message(encrypted_message)

        # Display the decrypted message
        self.encrypted_output.setText(decrypted_message)

        QMessageBox.information(self, "Decrypted Message", "Message decrypted successfully!")
        self.decrypt_input.clear()

class ControlPanel(QMainWindow):
    def __init__(self):
        super().__init__()

        # Main window settings
        self.setWindowTitle("Control Panel")
        self.setGeometry(100, 100, 600, 400)

        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setAlignment(Qt.AlignCenter)

        # Title
        self.title = QLabel("Control Panel")
        self.title.setStyleSheet("font-size: 24px; color: #333; margin-bottom: 20px;")
        self.layout.addWidget(self.title)

        # Buttons
        self.buttons_layout = QVBoxLayout()
        self.layout.addLayout(self.buttons_layout)

        # Drone button
        self.drone_button = QPushButton("Drone")
        self.drone_button.setStyleSheet("""
            QPushButton {
                padding: 15px 30px;
                font-size: 16px;
                color: #fff;
                background-color: #28a745;
                border: none;
                border-radius: 5px;
                
            }
            QPushButton:hover {
                background-color: #218838;
            }

        """)
        self.drone_button.clicked.connect(self.handle_drone_button)
        self.buttons_layout.addWidget(self.drone_button)

        # Messages button
        self.messages_button = QPushButton("Messages")
        self.messages_button.setStyleSheet("""
            QPushButton {
                padding: 15px 30px;
                font-size: 16px;
                color: #fff;
                background-color: #007bff;
                border: none;
                border-radius: 5px;
                
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            
        """)
        self.messages_button.clicked.connect(self.handle_messages_button)
        self.buttons_layout.addWidget(self.messages_button)

    def handle_drone_button(self):
        try:
            # Run main.py using subprocess
            subprocess.run(["python", "main.py"], check=True)
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "main.py file not found!")

    def handle_messages_button(self):
        messages = fetch_messages()
        dialog = MessageDialog(messages)
        dialog.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControlPanel()
    window.show()
    sys.exit(app.exec_())
