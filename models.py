# models.py
from pydantic import BaseModel
from typing import List, Optional

class Folder(BaseModel):
    id: str
    displayName: str
    childFolderCount: int

class EmailAddress(BaseModel):
    name: Optional[str]
    address: str

class FromField(BaseModel):
    emailAddress: EmailAddress

class Attachment(BaseModel):
    id: str
    name: str
    contentType: Optional[str]
    size: Optional[int]
    # add more as needed

class Message(BaseModel):
    id: str
    subject: Optional[str]
    from_: Optional[FromField] = None  # use alias in client
    receivedDateTime: Optional[str]
    body: Optional[dict]
    conversationId: Optional[str]
    inReplyTo: Optional[str]
    attachments: List[Attachment] = []
