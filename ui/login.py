# ui/login.py
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Input, Button

# Import the tab container screen
from ui.main_layout import MainLayoutScreen

class LoginScreen(Screen):
    def compose(self):
        yield Header(show_clock=True)
        yield Container(
            Static(
                r"""
██╗   ██╗ ██████╗ ██╗██████╗  ██████╗██╗  ██╗ █████╗ ████████╗
██║   ██║██╔═══██╗██║██╔══██╗██╔════╝██║  ██║██╔══██╗╚══██╔══╝
██║   ██║██║   ██║██║██║  ██║██║     ███████║███████║   ██║  
╚██╗ ██╔╝██║   ██║██║██║  ██║██║     ██╔══██║██╔══██║   ██║  
 ╚████╔╝ ╚██████╔╝██║██████╔╝╚██████╗██║  ██║██║  ██║   ██║  
  ╚═══╝   ╚═════╝ ╚═╝╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝  
                """,
                id="logo"
            ),

            Vertical(
                Static("── USER PROFILE ──", id="form_header"),
                Input(
                    placeholder="ENTER UNIQUE USERNAME",
                    id="username_input"
                ),
                Static("── NODE DESTINATION ──", id="form_header_2"),
                Horizontal(
                    Input(
                        placeholder="IP ADDRESS (e.g. 127.0.0.1)", 
                        id="ip_input"
                    ),
                    Input(
                        placeholder="PORT", 
                        id="port_input"
                    ),
                    id="network_row"
                ),
                Button(
                    "LOGIN",
                    id="connect_button"
                ),
                id="login_form"
            ),
            id="main_container"
        )
        yield Footer()

    def on_button_pressed(self, event):
        if event.button.id == "connect_button":
            username = self.query_one("#username_input").value
            ip = self.query_one("#ip_input").value
            port = self.query_one("#port_input").value

            self.notify(
                f"Connecting {username} to {ip}:{port}",
                timeout=3
            )

            # Switch completely away from login over to your main tab structure
            self.app.switch_screen(MainLayoutScreen())
