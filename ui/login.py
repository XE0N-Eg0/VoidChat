# ui/login.py
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Input, Button

# ==========================================
# PLACEHOLDER FUNCTIONS: 
# Replace the returns here with your actual 
# socket/networking logic.
# ==========================================
def get_local_ip():
    # TODO: add your socket gethostbyname logic here
    return "192.168.1.42" 

def get_node_port():
    # TODO: add your port assignment logic here
    return "8080"
# ==========================================

class LoginScreen(Screen):
    """The polished, input-restricted login screen."""
    
    # Ensure this points to where you save the CSS file
    CSS_PATH = "../styles/login.tcss"

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
                Static("── USER PROFILE ──", classes="form_header"),
                Input(
                    placeholder="ENTER UNIQUE USERNAME",
                    id="username_input"
                ),
                
                Static("── NODE DESTINATION ──", classes="form_header"),
                # Replaced Inputs with Static displays for read-only network info
                Horizontal(
                    Static(f"IP: {get_local_ip()}", classes="network_info"),
                    Static(f"PORT: {get_node_port()}", classes="network_info"),
                    id="network_row"
                ),
                
                Button(
                    "INITIALIZE CONNECTION",
                    id="connect_button",
                    variant="success"
                ),
                id="login_form"
            ),
            id="main_container"
        )
        yield Footer()

    def on_button_pressed(self, event):
        if event.button.id == "connect_button":
            # Grab the username, default to "Anonymous" if left blank
            username = self.query_one("#username_input").value or "Anonymous"
            ip = get_local_ip()
            port = get_node_port()

            # Fire off a UI notification
            self.notify(
                f"Connecting {username} to {ip}:{port}",
                timeout=3
            )

            # Assuming your app.py registers your main layout as "home"
            self.app.switch_screen("home")
            
    def on_input_submitted(self, event):
        """Allows the user to just hit ENTER in the username field to login."""
        if event.input.id == "username_input":
            # Trigger the button press programmatically
            self.query_one("#connect_button").press()