# app.py
from textual.app import App
from textual.binding import Binding
from textual.widgets import TabbedContent

from ui.login import LoginScreen
from ui.home import HomeScreen

class VoidChatApp(App):
    """VOID CHAT Main Application Entry Point."""
    
    TITLE = "VOID CHAT"
    
    SCREENS = {
        "login": LoginScreen,
        "home": HomeScreen
    }

    BINDINGS = [
        Binding("ctrl+1", "switch_tab('discovery_tab')", "Discovery", show=True),
        Binding("ctrl+2", "switch_tab('comms_tab')", "Comms", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    def on_mount(self) -> None:
        self.push_screen("login")

    def action_switch_tab(self, tab_id: str) -> None:
        """Safely switch tabs via global shortcut keys."""
        if isinstance(self.screen, HomeScreen):
            try:
                # Target the explicitly identified TabbedContent container
                tabs = self.screen.query_one("#tabs_container", TabbedContent)
                tabs.active = tab_id
            except Exception:
                # Suppress errors if elements are still loading during transits
                pass

if __name__ == "__main__":
    app = VoidChatApp()
    app.run()