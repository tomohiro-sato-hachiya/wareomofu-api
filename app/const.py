import os
import json
from enum import Enum, auto, IntEnum, unique

USERNAME_MAX_LENGTH = 128
REPORT_REASON_MAX_LENGTH = 100

STR_DEFAULT_MAX_LENGTH = 50000

THEME = {
    'title_max_length': 100,
    'description_max_length': STR_DEFAULT_MAX_LENGTH,
}

THESIS = {
    'content_max_length': STR_DEFAULT_MAX_LENGTH,
    'works_cited_max_length': STR_DEFAULT_MAX_LENGTH,
}

REPORT_DETAIL_MAX_LENGTH = 10000

COGNITO_INFO = json.loads(os.environ['COGNITO_INFO'])
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

SES_TEMPLATE_DIRECTORY = '/code/app/ses-template'

class ContentType(Enum):
    USER = auto()
    THEME = auto()
    THESIS = auto()
    COMMENT = auto()


@unique
class ThemeSortType(IntEnum):
    NEWER = 0
    OLDER = 1
    NUM_OF_THESES = 2
    START_EARLIER = 3
    START_LATER = 4
    EXPIRE_EARLIER = 5
    EXPIRE_LATER = 6


@unique
class ThesisSortType(IntEnum):
    NEWER = 0
    OLDER = 1
    NUM_OF_FAVORITES = 2
