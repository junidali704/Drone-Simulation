import pyodbc
import pyodbc
from cryptography.fernet import Fernet

# Initialize the Fernet key for encryption/decryption (ensure this key is the same throughout)
# fernet_key = Fernet.generate_key()
# fernet = Fernet(fernet_key)
# print(fernet_key)
def create_connection():
    connection = pyodbc.connect(r'DRIVER={SQL Server};SERVER=DESKTOP-K8BIO91\SQLEXPRESS;DATABASE=Drone')

    return connection


# def encrypt_message(message):
#     """Encrypts the given message using Fernet encryption."""
#     return fernet.encrypt(message.encode())

# def store_encrypted_message_in_db(encrypted_message, encrypted_passwordk):
#     """Stores the encrypted message and passwordk in the database."""
#     conn = create_connection()
#     cursor = conn.cursor()
#     cursor.execute(
#         "INSERT INTO messages (message, passwordk) VALUES (?, ?)",
#         (encrypted_message, encrypted_passwordk)
#     )
#     conn.commit()
#     cursor.close()
#     conn.close()

# def fetch_encrypted_messages():
#     """Fetches encrypted messages and their associated keys from the database."""
#     conn = create_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT message, passwordk FROM messages")
#     messages = cursor.fetchall()
#     cursor.close()
#     conn.close()
#     return messages