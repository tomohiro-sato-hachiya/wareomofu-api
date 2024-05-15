from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy.sql.expression import false, and_, or_, func
from . import models
from .. import schemas
from .. import const


def get_themes_common(
    db: Session,
    username: str,
    exclude_not_yet: bool,
    exclude_accepting: bool,
    exclude_expired: bool,
    free_words: List[str],
    sort_type: const.ThemeSortType,
    skip: int = 0,
    limit: int = 0,
    theme_ids: List[int] = None,
    datetime_null_is_earlier: bool = True
):
    result = db\
        .query(models.Theme)\
        .join(
            models.Thesis,
            and_(
                models.Thesis.theme_id == models.Theme.id,
                models.Thesis.is_suspended == false()
            ),
            isouter = True
        )
    conditions = [
        models.Theme.is_suspended == false(),
    ]
    if username:
        conditions.append(models.Theme.username == username)
    if theme_ids:
        conditions.append(models.Theme.id.in_(theme_ids))
    now = datetime.now()
    if exclude_not_yet:
        conditions.append(or_(
            models.Theme.start_datetime.is_(None),
            models.Theme.start_datetime < now
        ))
    if exclude_accepting:
        conditions.append(or_(
            and_(
                models.Theme.start_datetime.is_not(None),
                models.Theme.start_datetime > now
            ),
            and_(
                models.Theme.expire_datetime.is_not(None),
                models.Theme.expire_datetime < now
            )
        ))
    if exclude_expired:
        conditions.append(or_(
            models.Theme.expire_datetime.is_(None),
            models.Theme.expire_datetime > now
        ))
    if free_words:
        for free_word in free_words:
            like = f'%{free_word}%'
            conditions.append(or_(
                models.Theme.username.like(like),
                models.Theme.title.like(like),
                models.Theme.description.like(like)
            ))
    result = result.filter(*conditions).group_by(models.Theme.id)
    if sort_type is not None:
        if sort_type == const.ThemeSortType.NEWER:
            result = result.order_by(models.Theme.created_at.desc())
        elif sort_type == const.ThemeSortType.OLDER:
            result = result.order_by(models.Theme.created_at.asc())
        elif sort_type == const.ThemeSortType.NUM_OF_THESES:
            result = result.order_by(func.count(models.Thesis.id).desc())
        elif sort_type == const.ThemeSortType.START_EARLIER:
            if datetime_null_is_earlier:
                result = result.order_by(models.Theme.start_datetime.is_(None).desc())
            else:
                result = result.order_by(models.Theme.start_datetime.is_(None).asc())
            result = result.order_by(models.Theme.start_datetime.asc())
        elif sort_type == const.ThemeSortType.START_LATER:
            if datetime_null_is_earlier:
                result = result.order_by(models.Theme.start_datetime.is_(None).asc())
            else:
                result = result.order_by(models.Theme.start_datetime.is_(None).desc())
            result = result.order_by(models.Theme.start_datetime.desc())
        elif sort_type == const.ThemeSortType.EXPIRE_EARLIER:
            if datetime_null_is_earlier:
                result = result.order_by(models.Theme.expire_datetime.is_(None).desc())
            else:
                result = result.order_by(models.Theme.expire_datetime.is_(None).asc())
            result = result.order_by(models.Theme.expire_datetime.asc())
        elif sort_type == const.ThemeSortType.EXPIRE_LATER:
            if datetime_null_is_earlier:
                result = result.order_by(models.Theme.expire_datetime.is_(None).asc())
            else:
                result = result.order_by(models.Theme.expire_datetime.is_(None).desc())
            result = result.order_by(models.Theme.expire_datetime.desc())
    result = result.offset(skip)
    if limit > 0:
        result = result.limit(limit)
    return result


def get_themes(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    username: str = None,
    free_words: List[str] = None,
    theme_ids: List[int] = None,
    exclude_not_yet: bool = False,
    exclude_accepting: bool = False,
    exclude_expired: bool = False,
    sort_type: const.ThemeSortType = None,
    datetime_null_is_earlier: bool = True
):
    result = get_themes_common(
        db,
        username=username,
        exclude_not_yet=exclude_not_yet,
        exclude_accepting=exclude_accepting,
        exclude_expired=exclude_expired,
        free_words=free_words,
        skip=skip,
        limit=limit,
        theme_ids=theme_ids,
        sort_type=sort_type,
        datetime_null_is_earlier=datetime_null_is_earlier
    )
    result = result.all()
    return result


def get_themes_count(
    db: Session,
    username: str = None,
    free_words: List[str] = None,
    exclude_not_yet: bool = False,
    exclude_accepting: bool = False,
    exclude_expired: bool = False,
    sort_type: const.ThemeSortType = None,
    datetime_null_is_earlier: bool = True
):
    result = get_themes_common(
        db,
        username=username,
        exclude_not_yet=exclude_not_yet,
        exclude_accepting=exclude_accepting,
        exclude_expired=exclude_expired,
        free_words=free_words,
        sort_type=sort_type,
        datetime_null_is_earlier=datetime_null_is_earlier
    )
    count = result.count()
    return count


def get_theme(db: Session, theme_id: int, username: str = None):
    result = db.query(models.Theme)
    conditions = [
        models.Theme.id == theme_id,
        models.Theme.is_suspended == false(),
    ]
    if username:
        conditions.append(models.Theme.username == username)
    result = result.filter(*conditions).first()
    return result


def create_theme(db: Session, theme: schemas.ThemeCreate, username: str):
    db_theme = models.Theme(
        username=username,
        title=theme.title,
        description=theme.description,
        start_datetime=theme.start_datetime,
        expire_datetime=theme.expire_datetime,
        min_length=theme.min_length,
        max_length=theme.max_length
    )
    db.add(db_theme)
    db.commit()
    db.refresh(db_theme)
    return db_theme


def get_theses_common(
    db: Session,
    username: str,
    theme_id: int,
    free_words: List[str],
    sort_type: const.ThesisSortType,
    skip: int = 0,
    limit: int = 0
):
    result = db\
        .query(models.Thesis)\
        .join(
            models.Theme,
            and_(
                models.Theme.id == models.Thesis.theme_id,
                models.Theme.is_suspended == false()
            )
        )\
        .join(
            models.FavoriteThesis,
            models.FavoriteThesis.thesis_id == models.Thesis.id,
            isouter = True
        )
    conditions = [
        models.Thesis.is_suspended == false(),
    ]
    if username:
        conditions.append(models.Thesis.username == username)
    if theme_id:
        conditions.append(models.Thesis.theme_id == theme_id)
    if free_words:
        for free_word in free_words:
            like = f'%{free_word}%'
            conditions.append(or_(
                models.Thesis.username.like(like),
                models.Thesis.content.like(like),
                models.Thesis.works_cited.like(like)
            ))
    result = result.filter(*conditions).group_by(models.Thesis.id)
    if sort_type is not None:
        if sort_type == const.ThesisSortType.NEWER:
            result = result.order_by(models.Thesis.created_at.desc())
        elif sort_type == const.ThesisSortType.OLDER:
            result = result.order_by(models.Thesis.created_at.asc())
        elif sort_type == const.ThesisSortType.NUM_OF_FAVORITES:
            result = result.order_by(func.count(models.FavoriteThesis.id).desc())
    result = result.offset(skip)
    if limit > 0:
        result = result.limit(limit)
    return result


def get_theses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    username: str = None,
    theme_id: int = None,
    free_words: List[str] = None,
    sort_type: const.ThesisSortType = None
):
    result = get_theses_common(
        db,
        username=username,
        theme_id=theme_id,
        skip=skip,
        limit=limit,
        sort_type=sort_type,
        free_words=free_words
    )
    result = result.all()
    return result


def get_theses_count(
    db: Session,
    username: str = None,
    theme_id: int = None,
    sort_type: const.ThesisSortType = None,
    free_words: List[str] = None
):
    result = get_theses_common(
        db,
        username=username,
        theme_id=theme_id,
        sort_type=sort_type,
        free_words=free_words
    )
    count = result.count()
    return count


def get_thesis(db: Session, thesis_id: int, username: str = None):
    result = db\
        .query(models.Thesis)\
        .join(
            models.Theme,
            and_(
                models.Theme.id == models.Thesis.theme_id,
                models.Theme.is_suspended == false()
            )
        )
    conditions = [
        models.Thesis.id == thesis_id,
        models.Thesis.is_suspended == false()
    ]
    if username:
        conditions.append(models.Thesis.username == username)
    result = result.filter(*conditions).first()
    return result


def create_thesis(db: Session, thesis: schemas.ThesisCreate, username: str):
    db_thesis = models.Thesis(
        username=username,
        content=thesis.content,
        theme_id=thesis.theme_id,
        works_cited=thesis.works_cited
    )
    db.add(db_thesis)
    db.commit()
    db.refresh(db_thesis)
    return db_thesis


def get_favorite_thesis(
    db: Session,
    thesis_id: int,
    username: str
):
    conditions = [
        models.FavoriteThesis.thesis_id == thesis_id,
        models.FavoriteThesis.username == username
    ]
    favorite_thesis = db.query(models.FavoriteThesis).filter(*conditions).first()
    return favorite_thesis


def create_favorite_thesis(
    db: Session,
    thesis_id: int,
    username: str
):
    db_favorite_thesis = models.FavoriteThesis(
        thesis_id=thesis_id,
        username=username
    )
    db.add(db_favorite_thesis)
    db.commit()
    db.refresh(db_favorite_thesis)
    return db_favorite_thesis


def delete_favorite_thesis(
    db: Session,
    thesis_id: int,
    username: str
):
    favorite_thesis = get_favorite_thesis(
        db,
        thesis_id=thesis_id,
        username=username
    )
    db.delete(favorite_thesis)
    db.commit()


def get_user_favorites_common(
    db: Session,
    username: str,
    skip: int = 0,
    limit: int = 0
):
    result = db \
        .query(models.Thesis) \
        .join(
            models.FavoriteThesis,
            and_(
                models.FavoriteThesis.username == username,
                models.FavoriteThesis.thesis_id == models.Thesis.id
            )
        ) \
        .join(
            models.Theme,
            and_(
                models.Theme.id == models.Thesis.theme_id,
                models.Theme.is_suspended == false()
            )
        ) \
        .filter(models.Thesis.is_suspended == false())\
        .order_by(models.FavoriteThesis.created_at.desc()) \
        .offset(skip)
    if limit > 0:
        result = result.limit(limit)
    return result


def get_user_favorites(
    db: Session,
    username: str,
    skip: int = 0,
    limit: int = 100
):
    result = get_user_favorites_common(
        db,
        username=username,
        skip=skip,
        limit=limit
    )
    result = result.all()
    return result


def get_user_favorites_count(db: Session, username: str):
    result = get_user_favorites_common(
        db,
        username=username
    )
    count = result.count()
    return count


def get_comments_common(
    db: Session,
    thesis_id: int,
    skip: int = 0,
    limit: int = 0
):
    result = db.query(models.Comment)
    conditions = [
        models.Comment.is_suspended == false(),
        models.Comment.thesis_id == thesis_id,
    ]
    result = result.filter(*conditions).offset(skip)
    if limit > 0:
        result = result.limit(limit)
    return result


def get_comments(
    db: Session,
    thesis_id: int,
    skip: int = 0,
    limit: int = 100
):
    result = get_comments_common(
        db,
        thesis_id=thesis_id,
        skip=skip,
        limit=limit
    )
    result = result.all()
    return result


def get_comments_count(db: Session, thesis_id: int):
    result = get_comments_common(
        db,
        thesis_id=thesis_id
    )
    count = result.count()
    return count


def get_comment(db: Session, comment_id: int):
    result = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    return result


def create_comment(db: Session, thesis_id: int, username: str, content: str):
    comment = models.Comment(thesis_id=thesis_id, username=username, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def withdraw(db: Session, username: str):
    theses = db.query(models.Thesis).filter(models.Thesis.username == username).all()
    for thesis in theses:
        thesis.username = None
    themes = db.query(models.Theme).filter(models.Theme.username == username).all()
    for theme in themes:
        theme.username = None
    favorite_theses = db.query(models.FavoriteThesis).filter(models.FavoriteThesis.username == username).all()
    for favorite_thesis in favorite_theses:
        db.delete(favorite_thesis)
    comments = db.query(models.Comment).filter(models.Comment.username == username).all()
    for comment in comments:
        comment.username = None


def get_report_reasons(
        db: Session
):
    reasons = db.query(models.ReportReason).all()
    return reasons



def report_user(
    db: Session,
    target_username: str,
    reporter_username: str,
    report_reason_id: int,
    detail: str
):
    db_user_report = models.UserReport(
        target_username=target_username,
        reporter_username=reporter_username,
        report_reason_id=report_reason_id,
        detail=detail
    )
    db.add(db_user_report)
    db.commit()
    db.refresh(db_user_report)
    return db_user_report


def report_theme(
    db: Session,
    theme_id: int,
    reporter_username: str,
    target_username: str,
    report_reason_id: int,
    detail: str
):
    db_theme_report = models.ThemeReport(
        theme_id=theme_id,
        reporter_username=reporter_username,
        target_username=target_username,
        report_reason_id=report_reason_id,
        detail=detail
    )
    db.add(db_theme_report)
    db.commit()
    db.refresh(db_theme_report)
    return db_theme_report


def report_thesis(
    db: Session,
    thesis_id: int,
    reporter_username: str,
    target_username: str,
    report_reason_id: int,
    detail: str
):
    db_thesis_report = models.ThesisReport(
        thesis_id=thesis_id,
        reporter_username=reporter_username,
        target_username=target_username,
        report_reason_id=report_reason_id,
        detail=detail
    )
    db.add(db_thesis_report)
    db.commit()
    db.refresh(db_thesis_report)
    return db_thesis_report


def report_comment(
    db: Session,
    comment_id: int,
    reporter_username: str,
    target_username: str,
    report_reason_id: int,
    detail: str
):
    db_comment_report = models.CommentReport(
        comment_id=comment_id,
        reporter_username=reporter_username,
        target_username=target_username,
        report_reason_id=report_reason_id,
        detail=detail
    )
    db.add(db_comment_report)
    db.commit()
    db.refresh(db_comment_report)
    return db_comment_report


def create_or_read_email_notification_setting(
    db: Session,
    username: str
):
    setting = db\
        .query(models.EmailNotificationSetting)\
        .filter(models.EmailNotificationSetting.username==username)\
        .first()
    if setting:
        return setting
    else:
        db_setting = models.EmailNotificationSetting(username=username)
        db.add(db_setting)
        db.commit()
        db.refresh(db_setting)
        return db_setting


def update_email_notification_setting(
    db: Session,
    username: str,
    thesis: bool,
    favorite: bool,
    comment: bool
):
    db_setting = create_or_read_email_notification_setting(db, username=username)
    db_setting.thesis = thesis
    db_setting.favorite = favorite
    db_setting.comment = comment
    db.commit()
    db.refresh(db_setting)
    return db_setting
