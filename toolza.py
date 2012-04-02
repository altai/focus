import functools
import ldap
import MySQLdb
import urllib
from flask import (
    Flask, flash, render_template, request, redirect, url_for, session
)
from flaskext.wtf import Form, HiddenField, TextField, PasswordField, Required

def get_next_url():
    """
    Defines URI to redirect to after login.
    It is provided as element "next" of request.args(GET) or request.form(POST).
    If it is not we use endpoint name from  app config DEFAULT_NEXT_TO_LOGIN_VIEW.
    
    Context: view.
    """
    if request.method == 'POST':
        d = request.form
    else:
        d = request.args
    return d.get('next', url_for(app.config['DEFAULT_NEXT_TO_LOGIN_VIEW']))

def get_login_form():
    """
    Creates login form class with correct default value of "next".
    
    Context: view
    """
    class LoginForm(Form):
        next = HiddenField(default=get_next_url())
        username = TextField('Username', [Required()])
        password = PasswordField('Password', [Required()])
    return LoginForm


def mapped_dict(d, mapping):
    """
    Returns dictionary with keys coming from `mapping` and values taken
    from `d` for already translated keys (`mapping` values are keys in `d`).
    
    :param d: the dictionary providing values for result
    :param mapping: the dictionary defining mapping of keys
    
    Context: everywhere
    """
    return dict([(k, d[v]) for k, v in mapping.items()])

def obtain_token(username):
    """
    Returns last valid keystone token for the username.
    Returns None if nothing found.
    
    :param username: valid username
    
    Context: view
    """
    connection = MySQLdb.connect(
        **mapped_dict(app.config, {
            'host': 'DB_HOST',
            'user': 'DB_USER',
            'passwd': 'DB_PASS',
            'db': 'DB_NAME',
            'port': 'DB_PORT'
        })
    )
    with connection as cursor:
        cursor.execute('''
            select token.id 
            from users left join token on user_id 
            where users.name = %s and token.expires > now() 
            order by token.expires limit 1;''', (username,))
        if cursor.rowcount:
            return cursor.fetchone()[0]

# ldap validator
def are_ldap_authenticated(username, password):
    """
    Validates username and password with LDAP.
    
    Context: view
    """
    connection = ldap.initialize(app.config['LDAP_URI'])
    dn = 'uid=%s,%s' % (
        ldap.dn.escape_dn_chars(username),
        app.config['LDAP_BASEDN'])
    try:
        connection.simple_bind_s(dn, password)
    except ldap.INVALID_CREDENTIALS:
        return False
    else:
        return True
    finally:
        connection.unbind()
             
# config
SECRET_KEY = 'g.U(\x8cQ\xbc\xdb\\\xc3\x9a\xb2\xb6,\xec\xad(\xf8"2*\xef\x0bd'
NEXT_TO_LOGIN_ARG = 'next' # GET/POST field name to store next after login URL
DEFAULT_NEXT_TO_LOGIN_VIEW = 'index' # no next? redirect to this view
DEFAULT_NEXT_TO_LOGOUT_VIEW = 'index'
LDAP_URI = 'ldap://ns/' 
LDAP_BASEDN = 'ou=people,ou=griddynamics,dc=griddynamics,dc=net'
DB_HOST = ''
DB_PORT = 3306 # must be integer
DB_USER = ''
DB_PASS = ''
DB_NAME = ''

#app initialization
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('TOOLZA_CONFIG', silent=True)

def is_authenticated():
    return 'token' in session and 'username' in session

def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if is_authenticated():
            return view(*args, **kwargs)
        else:
            return redirect(
                '%s?%s' % (
                    url_for('login'),
                    urllib.urlencode(
                        {app.config['NEXT_TO_LOGIN_ARG']: request.path})))
    return wrapped

@app.context_processor
def auth_processor():
    d = {'authenticated': is_authenticated()}
    if is_authenticated():
        d['username'] = session['username']
    return d

@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = get_login_form()()
    if form.validate_on_submit():
        if are_ldap_authenticated(form.username.data, form.password.data):
            token = obtain_token(form.username.data)
            if token is not None:
                session['username'] = form.username.data
                session['token'] = token
                flash('You were logged in', 'success')
                return redirect(form.next.data)
            else:
                flash('Can not obtain an API token', 'error') 
        else:
            flash('Wrong username/password', 'error')
    return render_template('login.html', form=form)

@app.route('/')
@login_required
def index():
    return render_template('index.html', token=session['token'])

@app.route('/logout/')
def logout():
    session.pop('token', None)
    flash('You were logged out', 'success')
    return redirect(url_for(app.config['DEFAULT_NEXT_TO_LOGOUT_VIEW']))


if __name__ == '__main__':
    app.run()   
