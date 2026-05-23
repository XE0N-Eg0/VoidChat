# ui/home.py

from textual.app import ComposeResult
from textual.screen import Screen

from textual.containers import (
    Horizontal,
    Vertical,
    VerticalScroll,
)

from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    Input,
    TabbedContent,
    TabPane,
)

# =========================================================
# CUSTOM WIDGETS
# =========================================================

from ui.widgets.peer_card import (
    PeerCard,
    PeerSelected,
)

from ui.widgets.contact_card import (
    ContactCard,
    ContactSelected,
)

from ui.widgets.message_bubble import (
    MessageBubble,
)


class HomeScreen(Screen):
    """
    VOID CHAT Main Home Screen
    """

    CSS_PATH = "../styles/home.tcss"

    # =====================================================
    # SAMPLE CHAT DATA
    # Replace later with real networking/database logic
    # =====================================================

    CHAT_DATA = {

        "Alice": [
            ("recv", "Hello from Alice!"),
            ("send", "Hey Alice."),
            ("recv", "How are you?"),
        ],

        "Bob": [
            ("recv", "Yo."),
            ("send", "What's up Bob?"),
        ],

        "Charlie": [
            ("recv", "VOID online."),
            ("send", "Connection stable."),
        ],
    }

    # =====================================================
    # UI COMPOSITION
    # =====================================================

    def compose(self) -> ComposeResult:

        yield Header(show_clock=True)

        with TabbedContent(id="tabs_container"):

            # =================================================
            # DISCOVERY TAB
            # =================================================

            with TabPane(
                "Discovery",
                id="discovery_tab"
            ):

                with Horizontal(
                    classes="panel-container"
                ):

                    # =========================================
                    # LEFT : PEER LIST
                    # =========================================

                    with VerticalScroll(
                        classes="left-panel",
                        id="peer-list",
                    ):

                        yield Static(
                            "[bold cyan]Available Peers[/bold cyan]"
                        )

                        yield PeerCard(
                            "Raghunath Das",
                            "192.168.0.10",
                            online=True,
                        )

                        yield PeerCard(
                            "Alice",
                            "192.168.0.14",
                            online=True,
                        )

                        yield PeerCard(
                            "Bob",
                            "192.168.0.22",
                            online=False,
                        )

                    # =========================================
                    # RIGHT : PEER DETAILS
                    # =========================================

                    with Vertical(
                        classes="right-panel"
                    ):

                        yield Static(
                            (
                                "[bold cyan]Peer Details[/bold cyan]\n\n"
                                "No peer selected."
                            ),
                            id="selected-peer-info",
                        )

                        yield Button(
                            "Connect",
                            id="connect-btn",
                            variant="primary",
                        )

                        yield Static(
                            (
                                "[bold cyan]Incoming Requests[/bold cyan]\n\n"
                                "No requests yet."
                            ),
                            id="incoming-requests-panel",
                        )

            # =================================================
            # COMMUNICATIONS TAB
            # =================================================

            with TabPane(
                "Communications",
                id="comms_tab"
            ):

                with Horizontal(
                    classes="panel-container"
                ):

                    # =========================================
                    # LEFT : CONTACTS
                    # =========================================

                    with VerticalScroll(
                        id="chat-left-panel",
                        classes="left-panel",
                    ):

                        yield Static(
                            "[bold cyan]Contacts[/bold cyan]"
                        )

                        yield ContactCard(
                            "Alice",
                            online=True,
                            active=True,
                        )

                        yield ContactCard(
                            "Bob",
                            online=True,
                        )

                        yield ContactCard(
                            "Charlie",
                            online=False,
                        )

                    # =========================================
                    # RIGHT : CHAT AREA
                    # =========================================

                    with Vertical(
                        id="chat-right-panel",
                        classes="right-panel",
                    ):

                        # =====================================
                        # CHAT HISTORY
                        # =====================================

                        with VerticalScroll(
                            id="chat-history"
                        ):

                            yield Static(
                                "Welcome to VOID CHAT",
                                id="chat-welcome-text",
                            )

                            yield MessageBubble(
                                "Hello from Alice!",
                                sent_by_me=False,
                            )

                            yield MessageBubble(
                                "Hey Alice.",
                                sent_by_me=True,
                            )

                        # =====================================
                        # MESSAGE INPUT
                        # =====================================

                        with Horizontal(
                            id="chat-input-row"
                        ):

                            yield Input(
                                placeholder="Type message...",
                                id="chat-input",
                            )

                            yield Button(
                                "Send",
                                id="send-btn",
                                variant="success",
                            )

        yield Footer()

    # =====================================================
    # PEER SELECTION EVENT
    # =====================================================

    def on_peer_selected(
        self,
        event: PeerSelected
    ) -> None:

        peer_info = self.query_one(
            "#selected-peer-info",
            Static
        )

        peer_info.update(
            (
                "[bold cyan]Peer Details[/bold cyan]\n\n"

                f"[bold]Name:[/bold] "
                f"{event.peer_name}\n\n"

                f"[bold]IP:[/bold] "
                f"{event.peer_ip}\n\n"

                f"[bold]Status:[/bold] "
                f"{event.peer_status}"
            )
        )

    # =====================================================
    # CONTACT SWITCH EVENT
    # =====================================================

    def on_contact_selected(
        self,
        event: ContactSelected
    ) -> None:

        history = self.query_one(
            "#chat-history",
            VerticalScroll
        )

        # Remove old messages
        history.remove_children()

        # Get selected chat
        messages = self.CHAT_DATA.get(
            event.contact_name,
            []
        )

        # Add chat bubbles
        for direction, text in messages:

            history.mount(
                MessageBubble(
                    text,
                    sent_by_me=(
                        direction == "send"
                    )
                )
            )

    # =====================================================
    # SEND BUTTON
    # =====================================================

    def on_button_pressed(
        self,
        event: Button.Pressed
    ) -> None:

        # =============================================
        # SEND CHAT MESSAGE
        # =============================================

        if event.button.id == "send-btn":

            input_box = self.query_one(
                "#chat-input",
                Input
            )

            message = input_box.value.strip()

            if not message:
                return

            history = self.query_one(
                "#chat-history",
                VerticalScroll
            )

            history.mount(
                MessageBubble(
                    message,
                    sent_by_me=True,
                )
            )

            input_box.value = ""

        # =============================================
        # CONNECT BUTTON
        # =============================================

        elif event.button.id == "connect-btn":

            peer_info = self.query_one(
                "#selected-peer-info",
                Static
            )

            self.notify(
                "Connection request initiated.",
                timeout=3
            )