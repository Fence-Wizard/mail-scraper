from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Folder(BaseModel):
    id: str
    displayName: str
    childFolderCount: int = 0
    totalItemCount: int = 0

    model_config = ConfigDict(extra="allow")


class EmailAddress(BaseModel):
    name: Optional[str] = None
    address: str


class FromField(BaseModel):
    emailAddress: EmailAddress


class Attachment(BaseModel):
    id: str
    name: str
    contentType: Optional[str] = None
    size: Optional[int] = None

    model_config = ConfigDict(extra="allow")


class Message(BaseModel):
    id: str
    subject: Optional[str] = None
    from_: Optional[FromField] = Field(default=None, alias="from")
    receivedDateTime: Optional[str] = None
    body: Optional[dict] = None
    conversationId: Optional[str] = None
    inReplyTo: Optional[str] = None
    attachments: list[Attachment] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, extra="allow")
