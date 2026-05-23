# ui/home.py
from textual.app import ComposeResult
from textual.widgets import Static, Label

class HomeScreen(Static):
    """Layout module for the central Home Dashboard screen."""
    
    def compose(self) -> ComposeResult:
        yield Label(" Welcome to the central Node dashboard system.")
