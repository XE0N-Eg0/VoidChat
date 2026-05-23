# ui/widgets/message_bubble.py

from textual.containers import Container
from textual.widgets import Static


class MessageBubble(Container):
    """
    Chat message bubble widget.

    Supports:
    - Sent messages
    - Received messages
    - Different alignments
    - Bubble styling
    """

    def __init__(
        self,
        message: str,
        sent_by_me: bool = False,
    ) -> None:

        self.message = message
        self.sent_by_me = sent_by_me

        side_class = (
            "sent"
            if sent_by_me
            else "received"
        )

        super().__init__(
            Static(
                message,
                classes="chat-bubble"
            ),
            classes=f"message-wrapper {side_class}"
        )