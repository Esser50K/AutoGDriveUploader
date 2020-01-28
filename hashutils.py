import hashlib

BUF_SIZE = 65536

def hash_file(filepath):
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

def hash_string(s):
    md5 = hashlib.md5()
    md5.update(s)
    return md5.hexdigest()
