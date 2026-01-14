import logging
from logging import config
import os


LOGGING = {
    'version': 1,
    'formatters': {
        'precise': {
            'format': ('%(asctime)s %(process)-6d%(thread)-16d%(filename)-16s:'
                       '%(lineno)4d %(levelname)-6s: %(message)s'),
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'precise',
            'stream': 'ext://sys.stdout'
        }

    },
    'loggers': {
        'root': {
            'level': os.environ.get('LOG_LEVEL', 'INFO'),
            'handlers': ['console']
        }
    }
}

config.dictConfig(LOGGING)
logger = logging.getLogger('root')
logger.setLevel(logging.DEBUG)
logger.info('logger %s created', str(logger))
