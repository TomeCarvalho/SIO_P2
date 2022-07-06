import base64, os, json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# PASSWORD = b'master'
# SALT = b'\roy\x0bx>\x02\xe2W\xc3\x0bp#\x05\x91\xaf'
# KDF = PBKDF2HMAC(
#     algorithm=hashes.SHA256(),
#     length=32,
#     salt=SALT,
#     iterations=390000
# )
# KEY = base64.urlsafe_b64encode(KDF.derive(PASSWORD))
# FERNET = Fernet(KEY)

PASSWORD = os.environ['PASSWORD'].encode('utf-8')
SALT = b'\roy\x0bx>\x02\xe2W\xc3\x0bp#\x05\x91\xaf'
KDF_LENGTH = int(os.environ['KDF_LENGTH'])
ITERATIONS = int(os.environ['ITERATIONS'])

KDF = PBKDF2HMAC(algorithm=hashes.SHA256(), length=KDF_LENGTH, salt=SALT, iterations=ITERATIONS)
KEY = base64.urlsafe_b64encode(KDF.derive(PASSWORD))
FERNET = Fernet(KEY)

def encrypt(file):
    """Open an unencrypted file, return its encrypted form."""
    with open(file, 'r') as f:
        f_str = f.read()
        f_bytes = f_str.encode('utf-8')
        return FERNET.encrypt(f_bytes)

def encrypt_dict(dic):
    """Encrypt a dictionary."""
    dic_json = json.dumps(dic)
    dic_bytes = dic_json.encode('utf-8')
    return FERNET.encrypt(dic_bytes)

def decrypt(file):
    """Open an encrypted file, return its unencrypted form."""
    with open(file, 'rb') as f:
        f_bytes = f.read()
        return FERNET.decrypt(f_bytes).decode('utf-8')
