import logging
import logging.handlers

import gunicorn
import flask


CONFIG = flask.config.Config('/etc/focus/', 
                             {'LOG_MAX_BYTES': 1024 * 1024 * 100,
                              'LOG_BACKUP_COUNT': 12})
CONFIG.from_pyfile('gunicorn_config.py')


class Logger(gunicorn.glogging.Logger):
    """Uses RotatingFileHanler instead of FileHandler."""

    def _set_handler(self, log, output, fmt):
        # remove previous gunicorn log handler
        h = self._get_gunicorn_handler(log)
        if h:
            log.handlers.remove(h)

        if output == "-":
            h = logging.StreamHandler()
        else:
            gunicorn.util.check_is_writeable(output)
            h = logging.handlers.RotatingFileHandler(
                output, 
                maxBytes=CONFIG['LOG_MAX_BYTES'],
                backupCount=CONFIG['LOG_BACKUP_COUNT'])

        h.setFormatter(fmt)
        h._gunicorn = True
        log.addHandler(h)
