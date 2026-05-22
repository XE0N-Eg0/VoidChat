from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Header, Footer, Input, Label, Static

# --- THE LOGIC LAYER (Our Core Python Class) ---
class TextAnalyzer:
    """Pure business logic separated from the UI."""
    @staticmethod
    def count_words(text: str) -> int:
        if not text.strip():
            return 0
        return len(text.split())

    @staticmethod
    def count_chars(text: str) -> int:
        return len(text)


# --- THE UI LAYER (Textual App) ---
class WordCounterApp(App):
    """A terminal app connecting text analysis logic to the UI reactively."""
    
    # 1. Define Reactive Attributes (The UI automatically watches these)
    word_count = reactive(0)
    char_count = reactive(0)

    # Styling via internal TCSS (Textual CSS)
    CSS = """
    Screen {
        align: center middle;
        background: $background;
    }
    #input-container {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }
    #stats-container {
        width: 60;
        height: 5;
    }
    .stat-card {
        width: 1fr;
        height: 100%;
        content-align: center middle;
        border: tall $accent;
        background: $surface;
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the structural layout of the terminal window."""
        yield Header()
        
        with Vertical(id="input-container"):
            yield Label("Type something below to analyze:")
            yield Input(placeholder="Start typing...", id="text-input")
            
        with Horizontal(id="stats-container"):
            yield Static("Words: 0", id="word-card", classes="stat-card")
            yield Static("Characters: 0", id="char-card", classes="stat-card")
            
        yield Footer()

    # 2. Event Handler: Captures UI changes and passes them to our Logic
    def on_input_changed(self, event: Input.Changed) -> None:
        """Triggered automatically every time the user types a character."""
        user_text = event.value
        
        # Connect to business logic
        self.word_count = TextAnalyzer.count_words(user_text)
        self.char_count = TextAnalyzer.count_chars(user_text)

    # 3. Watchers: Automatically update the UI when Reactive variables change
    def watch_word_count(self, new_count: int) -> None:
        """Fires automatically whenever self.word_count is modified."""
        self.query_one("#word-card", Static).update(f"Words: {new_count}")

    def watch_char_count(self, new_count: int) -> None:
        """Fires automatically whenever self.char_count is modified."""
        self.query_one("#char-card", Static).update(f"Characters: {new_count}")


if __name__ == "__main__":
    app = WordCounterApp()
    app.run()