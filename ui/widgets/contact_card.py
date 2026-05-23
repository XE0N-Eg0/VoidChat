# ui/widgets/contact_card.py

from textual.widgets import Static
from textual.message import Message


class ContactSelected(Message):
    """
    Event fired when a contact card is clicked.
    """

    def __init__(self, contact_name: str) -> None:
        self.contact_name = contact_name
        super().__init__()


class ContactCard(Static):
    """
    A clickable contact widget used in the Communications tab.
    """

    def __init__(
        self,
        contact_name: str,
        online: bool = True,
        active: bool = False,
    ) -> None:

        self.contact_name = contact_name
        self.online = online

        status = "🟢" if online else "⚫"

        super().__init__(
            f"{status}  {contact_name}",
            classes="contact-card"
        )

        # Active contact highlight
        if active:
            self.add_class("-active")

    def on_click(self) -> None:
        """
        Fired when user clicks the contact.
        """

        # Remove active state from ALL contact cards
        for card in self.screen.query(ContactCard):
            card.remove_class("-active")

        # Activate clicked card
        self.add_class("-active")

        # Notify HomeScreen
        self.post_message(
            ContactSelected(
                self.contact_name
            )
        )