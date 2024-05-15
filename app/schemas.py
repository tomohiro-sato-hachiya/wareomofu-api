from typing import List, Union

from pydantic import BaseModel, Field
from pydantic.schema import datetime


class CountAndPages(BaseModel):
    count: int
    pages: List[int]


class AuthBase(BaseModel):
    access_token: str


class Withdraw(AuthBase):
    pass


class FavoriteThesisBase(BaseModel):
    thesis_id: int


class FavoriteThesisRead(FavoriteThesisBase, AuthBase):
    pass


class FavoriteThesisCreate(FavoriteThesisBase, AuthBase):
    pass


class FavoriteThesisDelete(FavoriteThesisBase, AuthBase):
    pass


class FavoriteThesis(FavoriteThesisBase):
    id: int
    username: str

    class Config:
        orm_mode = True


class ThesisBase(BaseModel):
    theme_id: int
    content: str
    works_cited: str


class ThesisCreate(ThesisBase, AuthBase):
    pass


class Thesis(ThesisBase):
    id: int
    username: Union[str, None] = None
    favorites: List[FavoriteThesis]
    created_at: datetime

    class Config:
        orm_mode = True


class ThesisIncludingSuspended(Thesis):
    is_suspended: bool


class ThemeBase(BaseModel):
    title: str
    description: str
    start_datetime: datetime = Field(default=None)
    expire_datetime: datetime = Field(default=None)
    min_length: int
    max_length: int = Field(default=None)


class ThemeCreate(ThemeBase, AuthBase):
    pass


class Theme(ThemeBase):
    id: int
    username: Union[str, None] = None
    max_length: int
    theses: List[ThesisIncludingSuspended]
    created_at: datetime

    class Config:
        orm_mode = True


class ReportReason(BaseModel):
    id: int
    reason: str

    class Config:
        orm_mode = True


class ReportBase(BaseModel):
    report_reason_id: int
    detail: str


class UserReport(AuthBase, ReportBase):
    target_username: str


class ThemeReport(AuthBase, ReportBase):
    theme_id: int


class ThesisReport(AuthBase, ReportBase):
    thesis_id: int


class CommentReport(AuthBase, ReportBase):
    comment_id: int


class CommentBase(BaseModel):
    thesis_id: int
    content: str


class CommentCreate(CommentBase, AuthBase):
    pass


class Comment(CommentBase):
    id: int
    username: Union[str, None] = None
    created_at: datetime

    class Config:
        orm_mode = True


class EmailNotificationSettingBase(BaseModel):
    thesis: bool
    favorite: bool
    comment: bool


class EmailNotificationSettingCreate(AuthBase):
    pass


class EmailNotificationSettingUpdate(EmailNotificationSettingBase, AuthBase):
    pass


class EmailNotificationSetting(EmailNotificationSettingBase):
    class Config:
        orm_mode = True
