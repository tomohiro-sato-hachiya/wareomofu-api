from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TEXT, BOOLEAN, DATETIME, TINYINT, BIGINT
from sqlalchemy.orm import relationship
from .. import const
from sqlalchemy.sql import func

from .database import Base


class Theme(Base):
    __tablename__ = 'themes'
    __table_args__ = ({'mysql_charset': 'utf8mb4'})

    id = Column(BIGINT(unsigned=True), primary_key=True, index=True)
    username = Column(VARCHAR(length=const.USERNAME_MAX_LENGTH), index=True, nullable=True)
    title = Column(TEXT, nullable=False)
    description = Column(TEXT, nullable=False)
    start_datetime = Column(DATETIME(timezone=True), index=True, nullable=True)
    expire_datetime = Column(DATETIME(timezone=True), index=True, nullable=True)
    min_length = Column(INTEGER(unsigned=True), nullable=False)
    max_length = Column(INTEGER(unsigned=True), nullable=False)
    is_suspended = Column(BOOLEAN, default=False, nullable=False)
    created_at = Column(DATETIME(timezone=True), server_default=func.now())
    updated_at = Column(DATETIME(timezone=True), onupdate=func.now())

    theses = relationship('Thesis', back_populates='theme')
    theme_reports = relationship('ThemeReport', back_populates='theme')


class Thesis(Base):
    __tablename__ = 'theses'
    __table_args__ = (UniqueConstraint('theme_id', 'username'), {'mysql_charset': 'utf8mb4'})

    id = Column(BIGINT(unsigned=True), primary_key=True, index=True)
    username = Column(VARCHAR(length=const.USERNAME_MAX_LENGTH), index=True, nullable=True)
    content = Column(TEXT, nullable=False)
    works_cited = Column(TEXT, nullable=False)
    is_suspended = Column(BOOLEAN, default=False, nullable=False)
    theme_id = Column(
        BIGINT(unsigned=True),
        ForeignKey('themes.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False
    )
    created_at = Column(DATETIME(timezone=True), server_default=func.now())
    updated_at = Column(DATETIME(timezone=True), onupdate=func.now())

    theme = relationship('Theme', back_populates='theses')
    thesis_reports = relationship('ThesisReport', back_populates='thesis')
    favorites = relationship('FavoriteThesis', back_populates='thesis')
    comments = relationship('Comment', back_populates='thesis')


class FavoriteThesis(Base):
    __tablename__ = 'favorite_theses'
    __table_args__ = (UniqueConstraint('thesis_id', 'username'), {'mysql_charset': 'utf8mb4'})

    id = Column(BIGINT(unsigned=True), primary_key=True, index=True)
    thesis_id = Column(
        BIGINT(unsigned=True),
        ForeignKey('theses.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False
    )
    username = Column(VARCHAR(length=const.USERNAME_MAX_LENGTH), index=True, nullable=False)
    created_at = Column(DATETIME(timezone=True), server_default=func.now())
    updated_at = Column(DATETIME(timezone=True), onupdate=func.now())

    thesis = relationship('Thesis', back_populates='favorites')


class Comment(Base):
    __tablename__ = 'comments'
    __table_args__ = ({'mysql_charset': 'utf8mb4'})

    id = Column(BIGINT(unsigned=True), primary_key=True, index=True)
    thesis_id = Column(
        BIGINT(unsigned=True),
        ForeignKey('theses.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False
    )
    username = Column(VARCHAR(length=const.USERNAME_MAX_LENGTH), index=True, nullable=True)
    content = Column(TEXT, nullable=False)
    is_suspended = Column(BOOLEAN, default=False, nullable=False)
    created_at = Column(DATETIME(timezone=True), server_default=func.now())
    updated_at = Column(DATETIME(timezone=True), onupdate=func.now())

    thesis = relationship('Thesis', back_populates='comments')
    comment_reports = relationship('CommentReport', back_populates='comment')


class ReportReason(Base):
    __tablename__ = 'report_reasons'
    __table_args__ = ({'mysql_charset': 'utf8mb4'})

    id = Column(TINYINT(unsigned=True), primary_key=True, index=True)
    reason = Column(VARCHAR(length=const.REPORT_REASON_MAX_LENGTH), index=True, nullable=False, unique=True)
    created_at = Column(DATETIME(timezone=True), server_default=func.now())
    updated_at = Column(DATETIME(timezone=True), onupdate=func.now())

    user_reports = relationship('UserReport', back_populates='reason')
    theme_reports = relationship('ThemeReport', back_populates='reason')
    thesis_reports = relationship('ThesisReport', back_populates='reason')
    comment_reports = relationship('CommentReport', back_populates='reason')


class UserReport(Base):
    __tablename__ = 'user_reports'
    __table_args__ = ({'mysql_charset': 'utf8mb4'})

    id = Column(BIGINT(unsigned=True), primary_key=True, index=True)
    target_username = Column(VARCHAR(length=const.USERNAME_MAX_LENGTH), index=True, nullable=False)
    reporter_username = Column(VARCHAR(length=const.USERNAME_MAX_LENGTH), index=True, nullable=False)
    report_reason_id = Column(
        TINYINT(unsigned=True),
        ForeignKey('report_reasons.id', onupdate='CASCADE', ondelete='RESTRICT'),
        nullable=False
    )
    detail = Column(TEXT, nullable=False)
    is_read = Column(BOOLEAN, default=False, nullable=False)
    created_at = Column(DATETIME(timezone=True), server_default=func.now())
    updated_at = Column(DATETIME(timezone=True), onupdate=func.now())

    reason = relationship('ReportReason', back_populates='user_reports')


class ThemeReport(Base):
    __tablename__ = 'theme_reports'
    __table_args__ = ({'mysql_charset': 'utf8mb4'})

    id = Column(BIGINT(unsigned=True), primary_key=True, index=True)
    theme_id = Column(
        BIGINT(unsigned=True),
        ForeignKey('themes.id', onupdate='CASCADE', ondelete='SET NULL'),
        nullable=True
    )
    reporter_username = Column(VARCHAR(length=const.USERNAME_MAX_LENGTH), index=True, nullable=True)
    target_username = Column(VARCHAR(length=const.USERNAME_MAX_LENGTH), index=True, nullable=False)
    report_reason_id = Column(
        TINYINT(unsigned=True),
        ForeignKey('report_reasons.id', onupdate='CASCADE', ondelete='RESTRICT'),
        nullable=False
    )
    detail = Column(TEXT, nullable=False)
    is_read = Column(BOOLEAN, default=False, nullable=False)
    created_at = Column(DATETIME(timezone=True), server_default=func.now())
    updated_at = Column(DATETIME(timezone=True), onupdate=func.now())

    reason = relationship('ReportReason', back_populates='theme_reports')
    theme = relationship('Theme', back_populates='theme_reports')


class ThesisReport(Base):
    __tablename__ = 'thesis_reports'
    __table_args__ = ({'mysql_charset': 'utf8mb4'})

    id = Column(BIGINT(unsigned=True), primary_key=True, index=True)
    thesis_id = Column(
        BIGINT(unsigned=True),
        ForeignKey('theses.id', onupdate='CASCADE', ondelete='SET NULL'),
        nullable=True
    )
    target_username = Column(VARCHAR(length=const.USERNAME_MAX_LENGTH), index=True, nullable=True)
    reporter_username = Column(VARCHAR(length=const.USERNAME_MAX_LENGTH), index=True, nullable=False)
    report_reason_id = Column(
        TINYINT(unsigned=True),
        ForeignKey('report_reasons.id', onupdate='CASCADE', ondelete='RESTRICT'),
        nullable=False
    )
    detail = Column(TEXT, nullable=False)
    is_read = Column(BOOLEAN, default=False, nullable=False)
    created_at = Column(DATETIME(timezone=True), server_default=func.now())
    updated_at = Column(DATETIME(timezone=True), onupdate=func.now())

    reason = relationship('ReportReason', back_populates='thesis_reports')
    thesis = relationship('Thesis', back_populates='thesis_reports')


class CommentReport(Base):
    __tablename__ = 'comment_reports'
    __table_args__ = ({'mysql_charset': 'utf8mb4'})

    id = Column(BIGINT(unsigned=True), primary_key=True, index=True)
    comment_id = Column(
        BIGINT(unsigned=True),
        ForeignKey('comments.id', onupdate='CASCADE', ondelete='SET NULL'),
        nullable=True
    )
    target_username = Column(VARCHAR(length=const.USERNAME_MAX_LENGTH), index=True, nullable=True)
    reporter_username = Column(VARCHAR(length=const.USERNAME_MAX_LENGTH), index=True, nullable=False)
    report_reason_id = Column(
        TINYINT(unsigned=True),
        ForeignKey('report_reasons.id', onupdate='CASCADE', ondelete='RESTRICT'),
        nullable=False
    )
    detail = Column(TEXT, nullable=False)
    is_read = Column(BOOLEAN, default=False, nullable=False)
    created_at = Column(DATETIME(timezone=True), server_default=func.now())
    updated_at = Column(DATETIME(timezone=True), onupdate=func.now())

    reason = relationship('ReportReason', back_populates='comment_reports')
    comment = relationship('Comment', back_populates='comment_reports')


class EmailNotificationSetting(Base):
    __tablename__ = 'email_notification_settings'
    __table_args__ = ({'mysql_charset': 'utf8mb4'})

    id = Column(BIGINT(unsigned=True), primary_key=True, index=True)
    username = Column(VARCHAR(length=const.USERNAME_MAX_LENGTH), index=True, nullable=False, unique=True)
    thesis = Column(BOOLEAN, default=True, nullable=False)
    favorite = Column(BOOLEAN, default=True, nullable=False)
    comment = Column(BOOLEAN, default=True, nullable=False)
    created_at = Column(DATETIME(timezone=True), server_default=func.now())
    updated_at = Column(DATETIME(timezone=True), onupdate=func.now())
