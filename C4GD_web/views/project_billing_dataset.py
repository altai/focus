from tasks import account_bill_show
from flask import g
from C4GD_web import app


class Dataset(object):
    def __init__(self, params=None, delayed=False):
        '''if delayed put task in celery
        invoke async task to call AccountBill.show and put results in db
        this call wont wait for the result of async task

        if not delayed then look in db fo result matching params
        if no result call for AccountBill.show, put results in db and return results
        if result exist use results from db
        '''
        if delayed:
            account_bill_show(params.account_id, g.user.id, g.tenant.id, app.config['BILLING_URL'], period_start=params.period_start, period_end=params.period_end, time_period=params.time_period)
        else:
            # what db?
            self.data = []
        pass


class Params(object):
    period_start = None
    period_end = None
    time_period = None

    def __init__(self, account_id, args={}):
        self.account_id = account_id
        if 'period_start' in args and 'period_end' in args:
            # control format of dates
            period_start = args['period_start']
            period_end = args['period_end']
        else:
            kind = args.get('kind', 'month')
            if kind == 'today':
                self.time_period = date.today().isoformat()
            elif kind == 'month':
                pass# API default is this month
            elif kind == 'year':
                self.time_period = date.today().year
            
    def lookup_key(self):
        return '%s:%s:%s:%s' % (
            self.account_id, self.period_start,
            self.period_end, self.time_period)
