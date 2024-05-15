from typing import List, Union

from fastapi import APIRouter, Path, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from datetime import datetime
import pytz

from ..sql import crud
from ..dependencies import get_db, get_slave_db
from .. import schemas
from .. import utils
from .. import const
from ..route import LoggingContextRoute

router = APIRouter()
router.route_class = LoggingContextRoute


@router.get('/constant/thesis', tags=['thesis', 'constant'])
async def get_thesis_constant():
    return const.THESIS


@router.get('/theses/{page}', tags=['thesis'], response_model=List[schemas.Thesis])
async def read_theses(
    page: int = Path(ge=1),
    username: Union[str, None] = None,
    theme_id: Union[int, None] = None,
    sort_type: Union[const.ThesisSortType, None] = None,
    free_words: Union[List[str], None] = Query(default=None),
    db: Session = Depends(get_slave_db)
):
    limit = 100
    skip = utils.get_skip(limit, page)
    theses = crud.get_theses(
        db,
        skip=skip,
        limit=limit,
        username=username,
        theme_id=theme_id,
        sort_type=sort_type,
        free_words=free_words
    )
    return theses


@router.get('/pages/theses', tags=['thesis', 'pages'], response_model=schemas.CountAndPages)
async def read_thesis_pages(
    username: Union[str, None] = None,
    theme_id: Union[int, None] = None,
    sort_type: Union[const.ThesisSortType, None] = None,
    free_words: Union[List[str], None] = Query(default=None),
    db: Session = Depends(get_slave_db)
):
    limit = 100
    count = crud.get_theses_count(
        db,
        username=username,
        theme_id=theme_id,
        sort_type=sort_type,
        free_words=free_words
    )
    max_page = (count // limit) + int((count % limit) > 0)
    if max_page == 0:
        max_page = 1
    pages = list(range(1, max_page + 1))
    result = {
        'count': count,
        'pages': pages
    }
    return result


@router.get('/thesis/{thesis_id}', tags=['thesis'], response_model=schemas.Thesis)
async def read_thesis(thesis_id: int = Path(ge=1), db: Session = Depends(get_slave_db)):
    thesis = crud.get_thesis(db, thesis_id=thesis_id)
    if thesis:
        return thesis
    else:
        detail = utils.get_not_found_message('小論文')
        raise HTTPException(status_code=404, detail=detail)


@router.post('/thesis/create', tags=['thesis'], response_model=schemas.Thesis)
async def create_thesis(thesis: schemas.ThesisCreate, db: Session = Depends(get_db)):
    theme = crud.get_theme(db, theme_id=thesis.theme_id)
    content_len = len(thesis.content)
    if theme:
        now = datetime.now()
        now = pytz.timezone('Asia/Tokyo').localize(now)
        if theme.start_datetime is not None:
            start_datetime = pytz.timezone('Asia/Tokyo').localize(theme.start_datetime)
            if start_datetime > now:
                raise HTTPException(status_code=403, detail='投稿受付開始日時前です')
        if theme.expire_datetime is not None:
            expire_datetime = pytz.timezone('Asia/Tokyo').localize(theme.expire_datetime)
            if expire_datetime < now:
                raise HTTPException(status_code=403, detail='投稿受付日時を過ぎました')
        if content_len < theme.min_length:
            raise HTTPException(status_code=403, detail='本文の文字数が最小文字数を満たしていません')
        if theme.max_length < content_len:
            raise HTTPException(status_code=403, detail='本文の文字数が最大文字数を超過しています')
    else:
        detail = utils.get_not_found_message('テーマ')
        raise HTTPException(status_code=404, detail=detail)
    username = utils.get_username(thesis.access_token)
    db_thesis = crud.create_thesis(db, thesis=thesis, username=username)
    if theme.username != username:
        email_notification_setting = crud.create_or_read_email_notification_setting(
            db,
            username=theme.username
        )
        if email_notification_setting.thesis:
            subject = 'テーマに小論文が投稿されました'
            with open(f'{const.SES_TEMPLATE_DIRECTORY}/thesis.txt', 'r') as f:
                main_template = f.read()
            summary_len_limit = 97
            if content_len > summary_len_limit:
                summary = f'{thesis.content[:summary_len_limit]}...'
            else:
                summary = thesis.content
            main = main_template.format(
                username,
                thesis.theme_id,
                db_thesis.id,
                summary
            )
            utils.send_email_notification(theme.username, subject, main)
    return db_thesis
