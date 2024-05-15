from typing import List

from fastapi import APIRouter, Path, Depends
from sqlalchemy.orm import Session

from ..sql import crud
from ..dependencies import get_db, get_slave_db
from .. import schemas
from .. import utils
from .. import const
from ..route import LoggingContextRoute

router = APIRouter()
router.route_class = LoggingContextRoute


@router.get('/pages/comments/{thesis_id}', tags=['comment', 'pages'], response_model=schemas.CountAndPages)
async def read_comment_pages(
    thesis_id: int = Path(ge=1),
    db: Session = Depends(get_slave_db)
):
    limit = 100
    count = crud.get_comments_count(db, thesis_id=thesis_id)
    max_page = (count // limit) + int((count % limit) > 0)
    if max_page == 0:
        max_page = 1
    pages = list(range(1, max_page + 1))
    result = {
        'count': count,
        'pages': pages
    }
    return result

@router.get('/comments/{thesis_id}/{page}', tags=['comment'], response_model=List[schemas.Comment])
async def read_comments(
    thesis_id: int = Path(ge=1),
    page: int = Path(ge=1),
    db: Session = Depends(get_slave_db)
):
    limit = 100
    skip = utils.get_skip(limit, page)
    comments = crud.get_comments(db, thesis_id=thesis_id, skip=skip, limit=limit)
    return comments


@router.post('/comment/create', tags=['comment'], response_model=bool)
async def create_comment(
    comment: schemas.CommentCreate,
    db: Session = Depends(get_db)
):
    username = utils.get_username(comment.access_token)
    crud.create_comment(db, thesis_id=comment.thesis_id, username=username, content=comment.content)
    thesis = crud.get_thesis(db, thesis_id=comment.thesis_id)
    if thesis.username != username:
        email_notification_setting = crud.create_or_read_email_notification_setting(
            db,
            username=thesis.username
        )
        if email_notification_setting.comment:
            subject = '小論文にコメントが投稿されました'
            with open(f'{const.SES_TEMPLATE_DIRECTORY}/comment.txt', 'r') as f:
                main_template = f.read()
            summary_len_limit = 97
            if len(comment.content) > summary_len_limit:
                summary = f'{comment.content[:summary_len_limit]}...'
            else:
                summary = comment.content
            main = main_template.format(
                username,
                comment.thesis_id,
                summary
            )
            utils.send_email_notification(thesis.username, subject, main)
    return True
