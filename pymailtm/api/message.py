from typing import List, Optional, Iterator

from pydantic import BaseModel, Field

from api.utils import join_path
from pymailtm.api.connection_manager import ConnectionManager
from pymailtm.api.auth import Token
from pymailtm.api.linked_collection import LinkedCollection, LinkedCollectionIterator
from pymailtm.api.logger import log
from pymailtm.api.utils import add_query


class Contact(BaseModel):
    """The contact model."""

    address: str
    name: str


class Attachment(BaseModel):
    """The attachment model."""

    id: str
    filename: str
    contentType: str
    disposition: bool
    transferEncoding: str
    related: bool
    size: int
    downloadUrl: str


class MessageIntro(BaseModel):
    """The message intro model which describes items from the field hydra_members in the response from the /messages endpoint.

    This model contains only a summary of the message and several fields are missing, notably the email body.
    The full message, which is available at the /messages/{id} endpoint, is represented by the `Message` class.
    """

    id: str
    msgid: str
    from_: Contact = Field(alias="from")
    to: List[Contact]
    subject: str
    intro: str
    seen: bool
    isDeleted: bool
    hasAttachments: bool
    size: int
    downloadUrl: str
    createdAt: str
    updatedAt: str
    accountId: str


class Message(MessageIntro):
    """The full message model. These are returned by the /messages/{id} endpoint."""

    cc: List[Contact]
    bcc: List[Contact]
    flagged: bool
    verifications: dict
    retention: bool
    retentionDate: str
    text: str
    html: List[str]
    attachments: List[Attachment]
    sourceUrl: str


class MessageIntros(LinkedCollection[MessageIntro]):
    """The message intros collection model. These are returned by the /messages endpoint."""


class MessageControllerIterators:

    def __init__(
        self, endpoint: str, connection_manager: ConnectionManager, token: Token
    ):
        self.endpoint = endpoint
        self.connection_manager = connection_manager
        self.token = token


class MessageController:
    """Class used to interact with the message API."""

    endpoint = "messages"

    def __init__(self, connection_manager: ConnectionManager, token: Token):
        self.connection_manager = connection_manager
        self.token = token

    @property
    def message_intros(self) -> Iterator[MessageIntro]:
        """Return a list of all message intros, taking case of pagination."""
        log("Messages iterator requested")
        return LinkedCollectionIterator[MessageIntros, MessageIntro](
            self.connection_manager, self.endpoint, MessageIntros, self.token
        )

    def get_message_intros_page(self, page: int = 1) -> Optional[MessageIntros]:
        """Return the message intros listed in a specific api response page."""
        log(f"Messages page requested: {page}")
        response = self.connection_manager.get(
            add_query(self.endpoint, {"page": page}), token=self.token
        )
        if response.status_code == 200:
            return MessageIntros(**response.json())
        return None

    def get_count(self) -> int:
        """Return the total number of available messages."""
        log("Messages count requested")
        return self.get_message_intros_page().hydra_totalItems

    def get_message(self, message_id: str) -> Optional[Message]:
        """Return the full message using the given id."""
        log(f"Full message requested: {message_id}")
        response = self.connection_manager.get(
            join_path(self.endpoint, message_id), token=self.token
        )
        if response.status_code == 200:
            return Message(**response.json())
        return None
