from textual.app import App
from ui.login import LoginScreen

class VoidChatApp(App):
    CSS_PATH = "main.tcss"

    def on_mount(self):
        self.push_screen(
        LoginScreen()
        )

if __name__ == "__main__":
    app = VoidChatApp()
    app.run()
