from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import boto3
from ..sql import crud
from ..dependencies import get_db
from .. import schemas
from .. import utils
from .. import const
from ..route import LoggingContextRoute

router = APIRouter()
router.route_class = LoggingContextRoute


@router.get('/users/{username}', tags=['user'], response_model=str)
async def get_user_profile(username: str):
    try:
        client = boto3.client('cognito-idp')
        user = client.admin_get_user(
            UserPoolId=const.COGNITO_INFO['user_pool_id'],
            Username=username
        )
        profile = ''
        for attribute in user['UserAttributes']:
            if attribute['Name'] == 'profile':
                profile = attribute['Value']
                break
        return profile
    except Exception as e:
        print(e)
        detail = 'ユーザー情報取得に失敗しました\nユーザーが存在しない可能性がございます'
        raise HTTPException(status_code=404, detail=detail)


@router.delete('/user/withdraw', tags=['user'], response_model=bool)
async def withdraw(form: schemas.Withdraw, db: Session = Depends(get_db)):
    username = utils.get_username(form.access_token)
    crud.withdraw(db, username=username)
    client = boto3.client('cognito-idp')
    client.delete_user(AccessToken=form.access_token)
    db.commit()
    return True


@router.post('/user/email_notification_setting', tags=['user'], response_model=schemas.EmailNotificationSetting)
async def read_email_notification_setting(
        form: schemas.EmailNotificationSettingCreate,
        db: Session = Depends(get_db)
):
    username = utils.get_username(form.access_token)
    setting = crud.create_or_read_email_notification_setting(db, username=username)
    return setting


@router.put('/user/email_notification_setting', tags=['user'], response_model=schemas.EmailNotificationSetting)
async def update_email_notification_setting(
        form: schemas.EmailNotificationSettingUpdate,
        db: Session = Depends(get_db)
):
    username = utils.get_username(form.access_token)
    setting = crud.update_email_notification_setting(
        db,
        username=username,
        thesis=form.thesis,
        favorite=form.favorite,
        comment=form.comment
    )
    return setting
