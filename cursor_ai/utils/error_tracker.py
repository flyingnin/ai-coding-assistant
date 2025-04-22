from datetime import datetime, timedelta

class ErrorTracker:
    def __init__(self, max_errors=50, error_expiry=timedelta(minutes=30)):
        self.errors = []
        self.max_errors = max_errors
        self.error_expiry = error_expiry
    
    def add_error(self, error_message, file_path=None, line_number=None):
        error = {
            "message": error_message,
            "file_path": file_path,
            "line_number": line_number,
            "timestamp": datetime.now()
        }
        
        self.errors.append(error)
        
        if len(self.errors) > self.max_errors:
            self.errors.pop(0)
            
    def get_errors(self, file_path=None):
        if file_path:
            return [e for e in self.errors if e["file_path"] == file_path]
        
        return self.errors
    
    def get_errors_as_string(self):
        if not self.errors:
            return "No errors"
            
        error_strings = []
        for error in self.errors:
            location = f"{error['file_path']}:{error['line_number']}" if error['file_path'] else "Unknown location"
            error_strings.append(f"{location} - {error['message']}")
            
        return '\\n'.join(error_strings)
