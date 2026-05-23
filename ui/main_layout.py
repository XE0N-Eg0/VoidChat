# ui/main_layout.py
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import TabbedContent, TabPane, Header, Footer

# Import your embedded pages
from ui.home import HomeScreen
from ui.chat import ChatScreen

class MainLayoutScreen(Screen):
    """The core container managing your functional interface tabs."""
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        # initial="home-pane" guarantees the home screen shows up first
        with TabbedContent(initial="home-pane"):
            with TabPane("Home System", id="home-pane"):
                yield HomeScreen()
                
            with TabPane("Secure Chat", id="chat-pane"):
                yield ChatScreen()
                
        yield Footer()
