class CursorContext:
    def __init__(self):
        self.open_files = []
        self.current_file = None
        self.current_file_content = None
        self.current_selection = None
        self.recent_actions = []
        self.tasks = []
        
    def update_open_files(self, files):
        self.open_files = files
        
    def update_current_file(self, file_path, content):
        self.current_file = file_path
        self.current_file_content = content
        
    def update_selection(self, selection):
        self.current_selection = selection
        
    def add_action(self, action_type, details):
        action = {
            "type": action_type,
            "details": details,
        }
        self.recent_actions.append(action)
        if len(self.recent_actions) > 20:
            self.recent_actions.pop(0)
            
    def add_task(self, task):
        self.tasks.append(task)
        
    def as_dict(self):
        return {
            "open_files": '\\n'.join(self.open_files) if self.open_files else "No files open",
            "current_file": self.current_file or "No file open",
            "current_file_content": self.current_file_content or "No content",
            "current_selection": self.current_selection or "No selection",
            "recent_actions": '\\n'.join([f"{a['type']}: {a['details']}" for a in self.recent_actions]) if self.recent_actions else "No recent actions",
            "tasks": '\\n'.join(self.tasks) if self.tasks else "No tasks",
            "errors": "No errors"
        }
