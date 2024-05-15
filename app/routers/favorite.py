from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from ..sql import crud
from ..dependencies import get_db, get_slave_db
from .. import schemas
from .. import utils
from .. import const
from ..route import LoggingContextRoute

router = APIRouter()
router.route_class = LoggingContextRoute


@router.get('/favorites/{page}', tags=['favorite'], response_model=List[schemas.Thesis])
async def read_user_favorites(
    username: str,
    page: int = Path(ge=1),
    db: Session = Depends(get_slave_db)
):
    limit = 100
    skip = utils.get_skip(limit, page)
    favorites = crud.get_user_favorites(db, username=username, skip=skip, limit=limit)
    return favorites


@router.get('/pages/favorites', tags=['favorite', 'pages'], response_model=schemas.CountAndPages)
async def read_user_favorite_pages(
    username: str,
    db: Session = Depends(get_slave_db)
):
    limit = 100
    count = crud.get_user_favorites_count(db, username=username)
    max_page = (count // limit) + int((count % limit) > 0)
    if max_page == 0:
        max_page = 1
    pages = list(range(1, max_page + 1))
    result = {
        'count': count,
        'pages': pages
    }
    return result


@router.post('/favorite/read', tags=['favorite'], response_model=bool)
async def read_favorites(favorite: schemas.FavoriteThesisRead, db: Session = Depends(get_slave_db)):
    username = utils.get_username(favorite.access_token)
    favorite_thesis = crud.get_favorite_thesis(
        db,
        thesis_id=favorite.thesis_id,
        username=username
    )
    if favorite_thesis:
        return True
    else:
        return False


@router.post('/favorite/like', tags=['favorite'], response_model=bool)
async def like(favorite: schemas.FavoriteThesisCreate, db: Session = Depends(get_db)):
    username = utils.get_username(favorite.access_token)
    crud.create_favorite_thesis(
        db,
        thesis_id=favorite.thesis_id,
        username=username
    )
    thesis = crud.get_thesis(db, thesis_id=favorite.thesis_id)
    if thesis.username != username:
        email_notification_setting = crud.create_or_read_email_notification_setting(
            db,
            username=thesis.username
        )
        if email_notification_setting.favorite:
            subject = '小論文がお気に入り登録されました'
            with open(f'{const.SES_TEMPLATE_DIRECTORY}/favorite.txt', 'r') as f:
                main_template = f.read()
            main = main_template.format(
                username,
                favorite.thesis_id
            )
            utils.send_email_notification(thesis.username, subject, main)
    return True


@router.delete('/favorite/dislike', tags=['favorite'], response_model=bool)
async def dislike(favorite: schemas.FavoriteThesisDelete, db: Session = Depends(get_db)):
    username = utils.get_username(favorite.access_token)
    crud.delete_favorite_thesis(
        db,
        thesis_id=favorite.thesis_id,
        username=username
    )
    return True
