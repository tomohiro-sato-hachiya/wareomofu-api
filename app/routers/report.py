from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import boto3
import json

from ..sql import crud, models
from ..dependencies import get_db, get_slave_db
from .. import schemas
from .. import utils
from .. import const
from ..route import LoggingContextRoute

router = APIRouter()
router.route_class = LoggingContextRoute


def check(reporter_username: str, target_username: str, detail: str):
    if reporter_username == target_username:
        detail = '通報者と通報対象者が同一です'
        raise HTTPException(status_code=403, detail=detail)
    if len(detail) > const.REPORT_DETAIL_MAX_LENGTH:
        detail = f'詳細の文字数が\n{const.REPORT_DETAIL_MAX_LENGTH}字を超過しています'
        raise HTTPException(status_code=403, detail=detail)


def publish_sns_alert(report, type: const.ContentType):
    dict_report = {'result': 'error'}
    if isinstance(report, models.UserReport):
        dict_report = {
            'id': report.id,
            'created_at': str(report.created_at),
        }
    elif isinstance(report, models.ThemeReport):
        dict_report = {
            'id': report.id,
            'theme_id': report.theme_id,
            'created_at': str(report.created_at),
        }
    elif isinstance(report, models.ThesisReport):
        dict_report = {
            'id': report.id,
            'thesis_id': report.thesis_id,
            'created_at': str(report.created_at),
        }
    elif isinstance(report, models.CommentReport):
        dict_report = {
            'id': report.id,
            'comment_id': report.comment_id,
            'created_at': str(report.created_at),
        }
    jsoned_report = json.dumps(dict_report)
    type_str = ''
    if type == const.ContentType.USER:
        type_str = 'ユーザー'
    elif type == const.ContentType.THEME:
        type_str = 'テーマ'
    elif type == const.ContentType.THESIS:
        type_str = '小論文'
    elif type == const.ContentType.COMMENT:
        type_str = 'コメント'
    subject = f'{type_str}に対する通報連絡'
    message = f'{subject}\n{jsoned_report}'
    client = boto3.client('sns')
    response = client.publish(
        TopicArn=const.SNS_TOPIC_ARN,
        Message=message,
        Subject=subject
    )
    print(response)


@router.get('/report/reasons', tags=['report'], response_model=List[schemas.ReportReason])
async def read_report_reasons(db: Session = Depends(get_slave_db)):
    reasons = crud.get_report_reasons(db)
    return reasons


@router.post('/report/user', tags=['user', 'report'],  response_model=bool)
async def report_user(report: schemas.UserReport, db: Session = Depends(get_db)):
    reporter_username = utils.get_username(report.access_token)
    check(reporter_username, report.target_username, report.detail)
    user_report = crud.report_user(
        db,
        target_username=report.target_username,
        reporter_username=reporter_username,
        report_reason_id=report.report_reason_id,
        detail=report.detail
    )
    publish_sns_alert(user_report, const.ContentType.USER)
    return True


@router.post('/report/theme', tags=['theme', 'report'],  response_model=bool)
async def report_theme(report: schemas.ThemeReport, db: Session = Depends(get_db)):
    reporter_username = utils.get_username(report.access_token)
    theme = crud.get_theme(db, theme_id=report.theme_id)
    if not theme:
        detail = utils.get_not_found_message('テーマ')
        raise HTTPException(status_code=404, detail=detail)
    check(reporter_username, theme.username, report.detail)
    theme_report = crud.report_theme(
        db,
        theme_id=report.theme_id,
        target_username=theme.username,
        reporter_username=reporter_username,
        report_reason_id=report.report_reason_id,
        detail=report.detail
    )
    publish_sns_alert(theme_report, const.ContentType.THEME)
    return True


@router.post('/report/thesis', tags=['thesis', 'report'],  response_model=bool)
async def report_thesis(report: schemas.ThesisReport, db: Session = Depends(get_db)):
    reporter_username = utils.get_username(report.access_token)
    thesis = crud.get_thesis(db, thesis_id=report.thesis_id)
    if not thesis:
        detail = utils.get_not_found_message('小論文')
        raise HTTPException(status_code=404, detail=detail)
    check(reporter_username, thesis.username, report.detail)
    thesis_report = crud.report_thesis(
        db,
        thesis_id=report.thesis_id,
        target_username=thesis.username,
        reporter_username=reporter_username,
        report_reason_id=report.report_reason_id,
        detail=report.detail
    )
    publish_sns_alert(thesis_report, const.ContentType.THESIS)
    return True


@router.post('/report/comment', tags=['comment', 'report'], response_model=bool)
async def report_comment(report: schemas.CommentReport, db: Session = Depends(get_db)):
    reporter_username = utils.get_username(report.access_token)
    comment = crud.get_comment(db, comment_id=report.comment_id)
    if not comment:
        detail = utils.get_not_found_message('コメント')
        raise HTTPException(status_code=404, detail=detail)
    check(reporter_username, comment.username, report.detail)
    comment_report = crud.report_comment(
        db,
        comment_id=report.comment_id,
        target_username=comment.username,
        reporter_username=reporter_username,
        report_reason_id=report.report_reason_id,
        detail=report.detail
    )
    publish_sns_alert(comment_report, const.ContentType.COMMENT)
    return True
