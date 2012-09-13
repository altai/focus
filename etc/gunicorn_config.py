import multiprocessing

bind = "0.0.0.0:8080"

formula_workers_count = multiprocessing.cpu_count() * 2 + 1

timeout = 86400
accesslog = '/var/log/focus/gunicorn.access-log'
errorlog = '/var/log/focus/gunicorn.error-log'

logger_class = 'focus.glogging.Logger'
LOG_MAX_BYTES = 1024 * 1024 * 100
LOG_BACKUP_COUNT = 12
