import multiprocessing

bind = "0.0.0.0:8080"
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 86400
accesslog = '/var/log/focus/gunicorn.access-log'
errorlog = '/var/log/focus/gunicorn.error-log'
