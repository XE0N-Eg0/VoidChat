# ui/widgets/peer_card.py

from textual.widgets import Static
from textual.message import Message


class PeerSelected(Message):
    """
    Event fired when a peer card is clicked.
    """

    def __init__(
        self,
        peer_name: str,
        peer_ip: str,
        peer_status: str,
    ) -> None:

        self.peer_name = peer_name
        self.peer_ip = peer_ip
        self.peer_status = peer_status

        super().__init__()


class PeerCard(Static):
    """
    Clickable peer card for the Discovery tab.
    """

    def __init__(
        self,
        peer_name: str,
        peer_ip: str,
        online: bool = True,
    ) -> None:

        self.peer_name = peer_name
        self.peer_ip = peer_ip
        self.online = online

        status_icon = "🟢" if online else "🟡"
        status_text = "ONLINE" if online else "AWAY"

        super().__init__(
            (
                f"{status_icon} {peer_name}\n"
                f"{peer_ip}\n"
                f"[dim]{status_text}[/dim]"
            ),
            classes="peer-card"
        )

    def on_click(self) -> None:
        """
        Triggered when user clicks a peer card.
        """

        # Remove selection from all peer cards
        for card in self.app.query(".peer-card"):
            card.remove_class("-active")

        # Highlight selected peer
        self.add_class("-active")

        # Notify HomeScreen
        self.post_message(
            PeerSelected(
                self.peer_name,
                self.peer_ip,
                "ONLINE" if self.online else "AWAY",
            )
        )