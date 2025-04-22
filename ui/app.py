"""
AI Coding Assistant - Desktop GUI

This module provides a desktop GUI for the AI Coding Assistant using PyQt6.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, 
    QTabWidget, QSplitter, QFileDialog, QMessageBox, QGroupBox,
    QListWidget, QListWidgetItem, QCheckBox, QSpinBox, QDialog,
    QProgressBar, QRadioButton, QButtonGroup, QScrollArea, QToolBar,
    QStatusBar, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor, QPalette, QAction
from PyQt6.QtWebEngineWidgets import QWebEngineView

from services.notification_service import NotificationService
from utils.openrouter import OpenRouterClient
from agents.ai_notification_agent import AINotificationAgent
import chromadb

# Configure logging
logger = logging.getLogger(__name__)

class ModelConfigDialog(QDialog):
    """Dialog for configuring AI models."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Model Configuration")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_openrouter_tab(), "OpenRouter")
        self.tabs.addTab(self.create_huggingface_tab(), "HuggingFace")
        
        # Recommendations panel
        recommendations = QGroupBox("Recommended Models")
        rec_layout = QVBoxLayout()
        rec_layout.addWidget(QLabel("🌟 Requirements Agent: Claude-3-Opus or GPT-4"))
        rec_layout.addWidget(QLabel("🌟 Coder Agent: Claude-3-Sonnet or GPT-4-Turbo"))
        rec_layout.addWidget(QLabel("🌟 Viewer Agent: GPT-4-Vision or Claude-3-Opus"))
        recommendations.setLayout(rec_layout)
        
        # Button box
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save Configuration")
        save_button.clicked.connect(self.save_configuration)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(recommendations)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Load existing configuration
        self.load_configuration()
        
    def create_openrouter_tab(self):
        """Create the OpenRouter tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel()
        instructions.setTextFormat(Qt.TextFormat.RichText)
        instructions.setWordWrap(True)
        instructions.setText("""
        <h3>How to get your OpenRouter API Key:</h3>
        <ol>
            <li>Visit <a href='https://openrouter.ai'>openrouter.ai</a> and create an account</li>
            <li>Go to your account settings</li>
            <li>Find the "API Keys" section</li>
            <li>Create a new key and copy it</li>
        </ol>
        <p>OpenRouter provides access to models from OpenAI, Anthropic, Google, and many others.</p>
        """)
        layout.addWidget(instructions)
        
        # API Key input
        key_group = QGroupBox("API Key")
        key_layout = QVBoxLayout()
        self.openrouter_key = QLineEdit()
        self.openrouter_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openrouter_key.setPlaceholderText("Enter your OpenRouter API key")
        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(lambda: self.test_api_key("openrouter"))
        key_layout.addWidget(self.openrouter_key)
        key_layout.addWidget(test_button)
        key_group.setLayout(key_layout)
        layout.addWidget(key_group)
        
        # Model selection
        models_group = QGroupBox("Default Models")
        models_layout = QVBoxLayout()
        
        # Requirements Agent Model
        req_layout = QHBoxLayout()
        req_layout.addWidget(QLabel("Requirements Agent:"))
        self.req_model = QComboBox()
        self.req_model.addItems([
            "claude-3-opus-20240229",
            "gpt-4-turbo-preview",
            "claude-3-sonnet-20240229",
            "gemini-pro",
            "llama-3-70b-chat"
        ])
        req_layout.addWidget(self.req_model)
        models_layout.addLayout(req_layout)
        
        # Coder Agent Model
        coder_layout = QHBoxLayout()
        coder_layout.addWidget(QLabel("Coder Agent:"))
        self.coder_model = QComboBox()
        self.coder_model.addItems([
            "claude-3-sonnet-20240229",
            "gpt-4-turbo-preview",
            "claude-3-opus-20240229",
            "gemini-pro",
            "llama-3-70b-chat"
        ])
        coder_layout.addWidget(self.coder_model)
        models_layout.addLayout(coder_layout)
        
        # Viewer Agent Model
        viewer_layout = QHBoxLayout()
        viewer_layout.addWidget(QLabel("Viewer Agent:"))
        self.viewer_model = QComboBox()
        self.viewer_model.addItems([
            "gpt-4-vision-preview",
            "claude-3-opus-20240229",
            "gemini-pro-vision",
            "claude-3-sonnet-20240229"
        ])
        viewer_layout.addWidget(self.viewer_model)
        models_layout.addLayout(viewer_layout)
        
        models_group.setLayout(models_layout)
        layout.addWidget(models_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
        
    def create_huggingface_tab(self):
        """Create the HuggingFace tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel()
        instructions.setTextFormat(Qt.TextFormat.RichText)
        instructions.setWordWrap(True)
        instructions.setText("""
        <h3>How to get your HuggingFace API Key:</h3>
        <ol>
            <li>Visit <a href='https://huggingface.co'>huggingface.co</a> and create an account</li>
            <li>Go to your account settings</li>
            <li>Find the "API Keys" section</li>
            <li>Create a new key and copy it</li>
        </ol>
        <p>HuggingFace provides access to thousands of open-source models.</p>
        """)
        layout.addWidget(instructions)
        
        # API Key input
        key_group = QGroupBox("API Key")
        key_layout = QVBoxLayout()
        self.huggingface_key = QLineEdit()
        self.huggingface_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.huggingface_key.setPlaceholderText("Enter your HuggingFace API key")
        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(lambda: self.test_api_key("huggingface"))
        key_layout.addWidget(self.huggingface_key)
        key_layout.addWidget(test_button)
        key_group.setLayout(key_layout)
        layout.addWidget(key_group)
        
        # Model selection
        models_group = QGroupBox("Default Models")
        models_layout = QVBoxLayout()
        
        # Model endpoint
        endpoint_layout = QHBoxLayout()
        endpoint_layout.addWidget(QLabel("Endpoint:"))
        self.hf_endpoint = QLineEdit()
        self.hf_endpoint.setPlaceholderText("Model endpoint (or leave empty for hosted inference API)")
        endpoint_layout.addWidget(self.hf_endpoint)
        models_layout.addLayout(endpoint_layout)
        
        # Default model
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Default Model:"))
        self.hf_model = QComboBox()
        self.hf_model.setEditable(True)
        self.hf_model.addItems([
            "meta-llama/Llama-3-70b-chat-hf",
            "meta-llama/Llama-3-8b-chat-hf",
            "mistralai/Mistral-7B-Instruct-v0.2",
            "TheBloke/Llama-2-13B-chat-GPTQ",
            "HuggingFaceH4/zephyr-7b-beta"
        ])
        model_layout.addWidget(self.hf_model)
        models_layout.addLayout(model_layout)
        
        models_group.setLayout(models_layout)
        layout.addWidget(models_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
        
    def test_api_key(self, provider):
        """Test the API key for the given provider."""
        try:
            if provider == "openrouter":
                api_key = self.openrouter_key.text()
                client = OpenRouterClient(api_key)
                success, _ = client.generate_response(
                    messages=[{"role": "user", "content": "Hello, this is a test."}],
                    max_tokens=10
                )
                
                if success:
                    QMessageBox.information(self, "Connection Test", "OpenRouter connection successful!")
                else:
                    QMessageBox.warning(self, "Connection Test", "OpenRouter connection failed. Please check your API key.")
                    
            elif provider == "huggingface":
                # Placeholder for HuggingFace API test
                QMessageBox.information(self, "Connection Test", "HuggingFace test functionality not yet implemented.")
                
        except Exception as e:
            QMessageBox.critical(self, "Connection Test Error", f"Error testing connection: {str(e)}")
            
    def save_configuration(self):
        """Save the configuration."""
        try:
            config = {
                "openrouter": {
                    "api_key": self.openrouter_key.text(),
                    "models": {
                        "requirements": self.req_model.currentText(),
                        "coder": self.coder_model.currentText(),
                        "viewer": self.viewer_model.currentText()
                    }
                },
                "huggingface": {
                    "api_key": self.huggingface_key.text(),
                    "endpoint": self.hf_endpoint.text(),
                    "default_model": self.hf_model.currentText()
                }
            }
            
            # Create config directory if it doesn't exist
            config_dir = Path(os.path.expandvars("%APPDATA%\\AI-Coding-Assistant"))
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save config
            with open(config_dir / "config.json", "w") as f:
                json.dump(config, f, indent=2)
                
            QMessageBox.information(self, "Configuration Saved", "Your configuration has been saved successfully.")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving configuration: {str(e)}")
            
    def load_configuration(self):
        """Load existing configuration."""
        try:
            config_path = Path(os.path.expandvars("%APPDATA%\\AI-Coding-Assistant\\config.json"))
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
                    
                # OpenRouter
                if "openrouter" in config:
                    self.openrouter_key.setText(config["openrouter"].get("api_key", ""))
                    models = config["openrouter"].get("models", {})
                    
                    if "requirements" in models:
                        index = self.req_model.findText(models["requirements"])
                        if index >= 0:
                            self.req_model.setCurrentIndex(index)
                            
                    if "coder" in models:
                        index = self.coder_model.findText(models["coder"])
                        if index >= 0:
                            self.coder_model.setCurrentIndex(index)
                            
                    if "viewer" in models:
                        index = self.viewer_model.findText(models["viewer"])
                        if index >= 0:
                            self.viewer_model.setCurrentIndex(index)
                            
                # HuggingFace
                if "huggingface" in config:
                    self.huggingface_key.setText(config["huggingface"].get("api_key", ""))
                    self.hf_endpoint.setText(config["huggingface"].get("endpoint", ""))
                    
                    if "default_model" in config["huggingface"]:
                        model = config["huggingface"]["default_model"]
                        index = self.hf_model.findText(model)
                        if index >= 0:
                            self.hf_model.setCurrentIndex(index)
                        else:
                            self.hf_model.setCurrentText(model)
                    
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")


class ProjectManager:
    """Project manager for the AI Coding Assistant."""
    
    def __init__(self, user_id="default"):
        """Initialize the project manager."""
        self.user_id = user_id
        self.user_dir = Path(os.path.expandvars(f"%APPDATA%\\AI-Coding-Assistant\\{user_id}"))
        self.user_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        self.chroma_dir = self.user_dir / "chromadb"
        self.chroma_dir.mkdir(exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_dir))
        
    def get_projects(self):
        """Get all projects for the user."""
        try:
            collections = self.chroma_client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Error getting projects: {str(e)}")
            return []
            
    def create_project(self, project_id):
        """Create a new project."""
        try:
            # Create collection in ChromaDB
            self.chroma_client.create_collection(project_id)
            
            # Create project directory
            project_dir = self.user_dir / "projects" / project_id
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Create project metadata
            metadata = {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "description": ""
            }
            
            with open(project_dir / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            return False
            
    def delete_project(self, project_id):
        """Delete a project."""
        try:
            # Delete collection from ChromaDB
            self.chroma_client.delete_collection(project_id)
            
            # Delete project directory
            project_dir = self.user_dir / "projects" / project_id
            if project_dir.exists():
                import shutil
                shutil.rmtree(project_dir)
                
            return True
            
        except Exception as e:
            logger.error(f"Error deleting project: {str(e)}")
            return False
            
    def save_context(self, project_id, context_data, context_id=None):
        """Save context to a project."""
        try:
            if context_id is None:
                context_id = f"context_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
            # Get the collection
            collection = self.chroma_client.get_or_create_collection(project_id)
            
            # Prepare data
            content = json.dumps(context_data)
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "type": context_data.get("type", "general")
            }
            
            # Add to collection
            collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[context_id]
            )
            
            return context_id
            
        except Exception as e:
            logger.error(f"Error saving context: {str(e)}")
            return None
            
    def get_context(self, project_id, context_id=None, query=None, limit=10):
        """Get context from a project."""
        try:
            collection = self.chroma_client.get_collection(project_id)
            
            if context_id:
                result = collection.get(ids=[context_id])
                return json.loads(result["documents"][0]) if result["documents"] else None
                
            elif query:
                result = collection.query(query_texts=[query], n_results=limit)
                return [json.loads(doc) for doc in result["documents"][0]] if result["documents"] else []
                
            else:
                result = collection.get()
                return [json.loads(doc) for doc in result["documents"]] if result["documents"] else []
                
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            return None if context_id else []


class MainWindow(QMainWindow):
    """Main window for the AI Coding Assistant."""
    
    def __init__(self):
        super().__init__()
        
        # Setup window
        self.setWindowTitle("AI Coding Assistant")
        self.setMinimumSize(1200, 800)
        
        # Initialize components
        self.project_manager = ProjectManager()
        self.current_project = None
        
        # Setup UI
        self.setup_ui()
        
        # Load projects
        self.load_projects()
        
    def setup_ui(self):
        """Setup the UI for the main window."""
        # Create central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel (projects and settings)
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Projects group
        projects_group = QGroupBox("Projects")
        projects_layout = QVBoxLayout()
        
        # Projects list
        self.projects_list = QListWidget()
        self.projects_list.itemClicked.connect(self.select_project)
        
        # Project buttons
        projects_buttons = QHBoxLayout()
        new_project_btn = QPushButton("New Project")
        new_project_btn.clicked.connect(self.create_new_project)
        delete_project_btn = QPushButton("Delete")
        delete_project_btn.clicked.connect(self.delete_project)
        projects_buttons.addWidget(new_project_btn)
        projects_buttons.addWidget(delete_project_btn)
        
        projects_layout.addWidget(self.projects_list)
        projects_layout.addLayout(projects_buttons)
        projects_group.setLayout(projects_layout)
        
        # Settings group
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        
        # API key config button
        api_key_btn = QPushButton("Configure API Keys & Models")
        api_key_btn.clicked.connect(self.open_model_config)
        settings_layout.addWidget(api_key_btn)
        
        settings_group.setLayout(settings_layout)
        
        # Add to left layout
        left_layout.addWidget(projects_group)
        left_layout.addWidget(settings_group)
        left_panel.setLayout(left_layout)
        
        # Right panel (main content)
        right_panel = QTabWidget()
        
        # Chat tab
        chat_tab = QWidget()
        chat_layout = QVBoxLayout()
        
        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        
        # Input area
        input_layout = QHBoxLayout()
        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("Describe what you want to build or ask a question about code...")
        self.chat_input.setMaximumHeight(100)
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(send_button)
        
        chat_layout.addWidget(self.chat_history)
        chat_layout.addLayout(input_layout)
        chat_tab.setLayout(chat_layout)
        
        # Code tab
        code_tab = QWidget()
        code_layout = QVBoxLayout()
        
        # Code editor
        code_editor_layout = QVBoxLayout()
        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText("Generated code will appear here...")
        self.code_editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.code_editor.setStyleSheet("font-family: monospace;")
        
        # Code buttons
        code_buttons = QHBoxLayout()
        save_code_btn = QPushButton("Save Code")
        save_code_btn.clicked.connect(self.save_code)
        copy_code_btn = QPushButton("Copy to Clipboard")
        copy_code_btn.clicked.connect(self.copy_code)
        code_buttons.addWidget(save_code_btn)
        code_buttons.addWidget(copy_code_btn)
        
        code_editor_layout.addWidget(self.code_editor)
        code_editor_layout.addLayout(code_buttons)
        code_layout.addLayout(code_editor_layout)
        code_tab.setLayout(code_layout)
        
        # Explanation tab
        explanation_tab = QWidget()
        explanation_layout = QVBoxLayout()
        
        # Web view for explanations
        self.explanation_view = QWebEngineView()
        self.explanation_view.setUrl(QUrl("about:blank"))
        explanation_layout.addWidget(self.explanation_view)
        explanation_tab.setLayout(explanation_layout)
        
        # Add tabs
        right_panel.addTab(chat_tab, "Chat")
        right_panel.addTab(code_tab, "Generated Code")
        right_panel.addTab(explanation_tab, "Explanation")
        
        # Add panels to splitter
        self.main_splitter.addWidget(left_panel)
        self.main_splitter.addWidget(right_panel)
        self.main_splitter.setSizes([300, 900])  # Default sizes
        
        # Add splitter to main layout
        main_layout.addWidget(self.main_splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Set central widget
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
    def load_projects(self):
        """Load projects from the project manager."""
        try:
            self.projects_list.clear()
            projects = self.project_manager.get_projects()
            
            for project in projects:
                self.projects_list.addItem(project)
                
            if projects:
                self.projects_list.setCurrentRow(0)
                self.select_project(self.projects_list.currentItem())
                
        except Exception as e:
            logger.error(f"Error loading projects: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error loading projects: {str(e)}")
            
    def create_new_project(self):
        """Create a new project."""
        try:
            project_name, ok = QLineEdit.getText(
                self, "New Project", "Enter project name:"
            )
            
            if ok and project_name:
                # Replace spaces with underscores and clean up name
                project_id = project_name.strip().replace(" ", "_").lower()
                
                # Create project
                if self.project_manager.create_project(project_id):
                    self.projects_list.addItem(project_id)
                    self.projects_list.setCurrentRow(self.projects_list.count() - 1)
                    self.select_project(self.projects_list.currentItem())
                    QMessageBox.information(self, "Success", f"Project '{project_name}' created successfully.")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to create project '{project_name}'.")
                    
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error creating project: {str(e)}")
            
    def delete_project(self):
        """Delete the current project."""
        try:
            if not self.current_project:
                QMessageBox.warning(self, "Warning", "No project selected.")
                return
                
            confirm = QMessageBox.question(
                self, "Confirm Delete", 
                f"Are you sure you want to delete project '{self.current_project}'? This will permanently delete all project data.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                if self.project_manager.delete_project(self.current_project):
                    # Remove from list
                    row = self.projects_list.currentRow()
                    self.projects_list.takeItem(row)
                    
                    # Clear current project
                    self.current_project = None
                    
                    # Select another project if available
                    if self.projects_list.count() > 0:
                        self.projects_list.setCurrentRow(0)
                        self.select_project(self.projects_list.currentItem())
                        
                    QMessageBox.information(self, "Success", "Project deleted successfully.")
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete project.")
                    
        except Exception as e:
            logger.error(f"Error deleting project: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error deleting project: {str(e)}")
            
    def select_project(self, item):
        """Select a project."""
        if item:
            self.current_project = item.text()
            self.status_bar.showMessage(f"Current project: {self.current_project}")
            
            # Clear chat history and code editor
            self.chat_history.clear()
            self.code_editor.clear()
            self.explanation_view.setUrl(QUrl("about:blank"))
            
    def open_model_config(self):
        """Open the model configuration dialog."""
        dialog = ModelConfigDialog(self)
        dialog.exec()
        
    def send_message(self):
        """Send a message to the AI assistant."""
        try:
            if not self.current_project:
                QMessageBox.warning(self, "Warning", "Please select or create a project first.")
                return
                
            # Get message from input
            message = self.chat_input.toPlainText().strip()
            if not message:
                return
                
            # Clear input
            self.chat_input.clear()
            
            # Add message to chat history
            self.chat_history.append(f"<p><strong>You:</strong> {message}</p>")
            
            # Set status
            self.status_bar.showMessage("Thinking...")
            
            # Process message (placeholder)
            # In a real implementation, this would interact with the agent system
            # For now, we'll just display a static response
            
            # Simulate thinking time
            QTimer.singleShot(1500, lambda: self.handle_ai_response(message))
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error sending message: {str(e)}")
            
    def handle_ai_response(self, message):
        """Handle AI response (placeholder)."""
        # This is a placeholder - in a real implementation, this would interact with the agent system
        response = "I'm analyzing your request. I'll help you build this by breaking it down into steps. First, let me ask you a few questions to understand your requirements better."
        
        # Add response to chat history
        self.chat_history.append(f"<p><strong>AI Assistant:</strong> {response}</p>")
        
        # Update status
        self.status_bar.showMessage("Ready")
        
        # Save the interaction to the project context
        self.save_interaction(message, response)
        
    def save_interaction(self, message, response):
        """Save interaction to project context."""
        if not self.current_project:
            return
            
        context_data = {
            "type": "chat",
            "timestamp": datetime.now().isoformat(),
            "user_message": message,
            "ai_response": response
        }
        
        self.project_manager.save_context(self.current_project, context_data)
        
    def save_code(self):
        """Save generated code to a file."""
        try:
            code = self.code_editor.toPlainText()
            if not code:
                QMessageBox.warning(self, "Warning", "No code to save.")
                return
                
            # Open file dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Code", "", "All Files (*);;Python Files (*.py);;JavaScript Files (*.js)"
            )
            
            if file_path:
                with open(file_path, "w") as f:
                    f.write(code)
                QMessageBox.information(self, "Success", f"Code saved to {file_path}")
                
        except Exception as e:
            logger.error(f"Error saving code: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error saving code: {str(e)}")
            
    def copy_code(self):
        """Copy code to clipboard."""
        code = self.code_editor.toPlainText()
        if code:
            QApplication.clipboard().setText(code)
            self.status_bar.showMessage("Code copied to clipboard", 3000)
        else:
            QMessageBox.warning(self, "Warning", "No code to copy.")


def run_app():
    """Run the desktop application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Run the application
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_app()) 