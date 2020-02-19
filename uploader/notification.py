# Notification Types
FILE_CREATED_NOTIFICATION = "FILE_CREATED"
FILE_UPDATED_NOTIFICATION = "FILE_UPDATED"  # TODO id of file should be inode and should save last modified timestamp
FILE_MOVED_NOTIFICATION = "FILE_MOVED"  # TODO implement moving files logic in drive service
FILE_DELETED_NOTIFICATION = "FILE_DELETED"

class Notification:
    def __init__(self):
        pass