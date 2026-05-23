# ui/chat.py
from textual.app import ComposeResult
from textual.widgets import Static, Label, Input

class ChatScreen(Static):
    """Layout module for the messaging client interface."""
    
    def compose(self) -> ComposeResult:
        yield Label(" Connected to secure communications pipeline.")
        yield Input(placeholder="Type Message...")
