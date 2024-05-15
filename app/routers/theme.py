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


@router.get('/constant/theme', tags=['theme', 'constant'])
async def get_thesis_constant():
    return const.THEME


def get_themes_parameters(
    exclude_not_yet: int,
    exclude_accepting: int,
    exclude_expired: int,
    sort_type: const.ThemeSortType,
    datetime_null_is_earlier: int
) -> dict:
    exclude_not_yet = exclude_not_yet == 1
    exclude_accepting = exclude_accepting == 1
    exclude_expired = exclude_expired == 1
    if sort_type is None:
        sort_type = const.ThemeSortType.NEWER
    datetime_null_is_earlier = \
        (datetime_null_is_earlier is None) \
        or datetime_null_is_earlier == 1
    result = {
        'exclude_not_yet': exclude_not_yet,
        'exclude_accepting': exclude_accepting,
        'exclude_expired': exclude_expired,
        'sort_type': sort_type,
        'datetime_null_is_earlier': datetime_null_is_earlier
    }
    return result

@router.get('/themes/{page}', tags=['theme'], response_model=List[schemas.Theme])
async def read_themes(
    page: int = Path(ge=1),
    username: Union[str, None] = None,
    theme_ids: Union[List[int], None] = Query(default=None),
    exclude_not_yet: Union[int, None] = None,
    exclude_accepting: Union[int, None] = None,
    exclude_expired: Union[int, None] = None,
    free_words: Union[List[str], None] = Query(default=None),
    sort_type: Union[const.ThemeSortType, None] = None,
    datetime_null_is_earlier: Union[int, None] = None,
    db: Session = Depends(get_slave_db)
):
    limit = 100
    skip = utils.get_skip(limit, page)
    parameters = get_themes_parameters(
        exclude_not_yet,
        exclude_accepting,
        exclude_expired,
        sort_type,
        datetime_null_is_earlier
    )
    themes = crud.get_themes(
        db,
        skip=skip,
        limit=limit,
        username=username,
        theme_ids=theme_ids,
        exclude_not_yet=parameters['exclude_not_yet'],
        exclude_accepting=parameters['exclude_accepting'],
        exclude_expired=parameters['exclude_expired'],
        free_words=free_words,
        sort_type=parameters['sort_type'],
        datetime_null_is_earlier=parameters['datetime_null_is_earlier']
    )
    return themes


@router.get('/pages/themes', tags=['theme', 'pages'], response_model=schemas.CountAndPages)
async def read_theme_pages(
    username: Union[str, None] = None,
    exclude_not_yet: Union[int, None] = None,
    exclude_accepting: Union[int, None] = None,
    exclude_expired: Union[int, None] = None,
    free_words: Union[List[str], None] = Query(default=None),
    sort_type: Union[const.ThemeSortType, None] = None,
    datetime_null_is_earlier: Union[int, None] = None,
    db: Session = Depends(get_slave_db)
):
    limit = 100
    parameters = get_themes_parameters(
        exclude_not_yet,
        exclude_accepting,
        exclude_expired,
        sort_type,
        datetime_null_is_earlier
    )
    count = crud.get_themes_count(
        db,
        username=username,
        exclude_not_yet=parameters['exclude_not_yet'],
        exclude_accepting=parameters['exclude_accepting'],
        exclude_expired=parameters['exclude_expired'],
        free_words=free_words,
        sort_type=parameters['sort_type'],
        datetime_null_is_earlier=parameters['datetime_null_is_earlier']
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


@router.get('/theme/{theme_id}', tags=['theme'], response_model=schemas.Theme)
async def read_theme(theme_id: int = Path(ge=1), db: Session = Depends(get_slave_db)):
    theme = crud.get_theme(db, theme_id=theme_id)
    if theme:
        return theme
    else:
        detail = utils.get_not_found_message('テーマ')
        raise HTTPException(status_code=404, detail=detail)


@router.post('/theme/create', tags=['theme'], response_model=schemas.Theme)
async def create_theme(theme: schemas.ThemeCreate, db: Session = Depends(get_db)):
    empty_fail_format = '{}を入力してください'
    if not theme.title:
        detail = empty_fail_format.format('タイトル')
        raise HTTPException(status_code=403, detail=detail)
    if not theme.description:
        detail = empty_fail_format.format('説明文')
        raise HTTPException(status_code=403, detail=detail)
    if theme.min_length == 0:
        detail = empty_fail_format.format('最小文字数')
        raise HTTPException(status_code=403, detail=detail)
    if len(theme.title) > const.THEME['title_max_length']:
        raise HTTPException(status_code=403, detail='タイトルの文字数が長過ぎます')
    if len(theme.description) > const.THEME['description_max_length']:
        raise HTTPException(status_code=403, detail='説明文の文字数が長過ぎます')
    if theme.start_datetime is not None\
            and theme.expire_datetime is not None\
            and theme.start_datetime >= theme.expire_datetime:
        raise HTTPException(status_code=403, detail='受付開始日時が受付終了日時より後か同日同時刻に指定されています')
    now = datetime.now()
    now = pytz.timezone('Asia/Tokyo').localize(now)
    timezone = 'Asia/Tokyo'
    if theme.start_datetime is not None:
        try:
            start_datetime = pytz.timezone(timezone).localize(theme.start_datetime)
        except Exception:
            start_datetime = theme.start_datetime
        if start_datetime < now:
            raise HTTPException(status_code=403, detail='受付開始日時が過ぎています')
    if theme.expire_datetime is not None:
        try:
            expire_datetime = pytz.timezone(timezone).localize(theme.expire_datetime)
        except Exception:
            expire_datetime = theme.expire_datetime
        if expire_datetime < now:
            raise HTTPException(status_code=403, detail='受付終了日時が過ぎています')
    default_content_max_length = const.THESIS['content_max_length']
    if (theme.max_length is not None) and (theme.min_length > theme.max_length):
        raise HTTPException(status_code=403, detail='小論文の最小文字数が、最大文字数より大きく指定されています')
    if theme.max_length is None:
        theme.max_length = default_content_max_length
    elif default_content_max_length < theme.max_length:
        detail = f'小論文の最大文字数は{"{:,}".format(default_content_max_length)}字までに指定できます'
        raise HTTPException(status_code=403, detail=detail)
    username = utils.get_username(theme.access_token)
    return crud.create_theme(db, theme=theme, username=username)
