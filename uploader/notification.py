# Notification Types
FILE_CREATED_NOTIFICATION = "FILE_CREATED"
FILE_UPLOAD_PROGRESS_NOTIFICATION = "FILE_UPLOAD_PROGRESS"
FILE_UPDATED_NOTIFICATION = "FILE_UPDATED"
FILE_MOVED_NOTIFICATION = "FILE_MOVED"
FILE_DELETED_NOTIFICATION = "FILE_DELETED"
REMOTE_SCAN_NOTIFICATION = "REMOTE_SCAN"


class Notification:
    def __init__(self, type, file_doc={}):
        self.type = type
        self.file_doc = file_doc


class FileCreatedNotification(Notification):
    def __init__(self, file_doc):
        super().__init__(FILE_CREATED_NOTIFICATION, file_doc)


class FileUpdatedNotification(Notification):
    def __init__(self, file_doc):
        super().__init__(FILE_UPDATED_NOTIFICATION, file_doc)


class FileDeletedNotification(Notification):
    def __init__(self, file_doc):
        super().__init__(FILE_DELETED_NOTIFICATION, file_doc)


class FileUploadProgressNotification(Notification):
    def __init__(self, file_doc, progress, in_failure):
        super().__init__(FILE_UPLOAD_PROGRESS_NOTIFICATION, file_doc)
        self.progress = progress
        self.in_failure = in_failure


class FileMovedNotification(Notification):
    def __init__(self, file_doc, previous_folder_doc, new_folder_doc):
        super().__init__(FILE_MOVED_NOTIFICATION, file_doc)
        self.previous_folder_doc = previous_folder_doc
        self.new_folder_doc = new_folder_doc


class RemoteScanNotification:
    def __init__(self, remote_files):
        self.type = REMOTE_SCAN_NOTIFICATION
        self.remote_files = remote_files
