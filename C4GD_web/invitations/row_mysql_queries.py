import urlparse
import MySQLdb

from C4GD_web import app


conn_creds = urlparse.urlsplit(app.config['INVITATIONS_URL'])
cred_kw = dict(host=conn_creds.hostname,
    user=conn_creds.username,
    db=conn_creds.path[1:])
if conn_creds.password:
    cred_kw['passwd'] = conn_creds.password
conn = MySQLdb.connect(**cred_kw)


cursor = conn.cursor()


# invitations
def save_invitation(email, hash, complete, role):
    query = "INSERT INTO invitations.invitations SET "+\
        "email='%s'," % email +\
        "hash='%s'," % hash +\
        "complete=%d," % (1 if complete else 0) +\
        "role='%s';" % role
    cursor.execute(query) 
    conn.commit()

    
def get_invitation_by_hash(invitation_hash):
    query = """
        SELECT * 
        FROM invitations.invitations 
        WHERE invitations.hash = '%s'""" % invitation_hash
    cursor.execute(query)
    row = cursor.fetchone()
    return row


def update_invitation(id, email, hash, complete):
    query = """
        UPDATE invitations.invitations 
        SET
         email='%s',
         hash='%s',
         complete=%d 
        WHERE id=%d""" % (email, hash, 1 if complete else 0, id)
    cursor.execute(query) 
    conn.commit()

       
#masks
def get_masks():
    query = """SELECT email_mask FROM invitations.email_masks;"""
    cursor.execute(query)
    rows = cursor.fetchall()
    return rows


# password recovery
def save_recovery(email, hash, complete):
    query = "INSERT INTO invitations.recovery_requests SET "+\
        "email='%s'," % email +\
        "hash='%s'," % hash +\
        "complete=%d;" % (1 if complete else 0)
    cursor.execute(query) 
    conn.commit()

    
def get_recovery_request_by_hash(recovery_hash):
    query = """
        SELECT * 
        FROM invitations.recovery_requests 
        WHERE recovery_requests.hash = '%s'""" % recovery_hash
    cursor.execute(query)
    row = cursor.fetchone()
    return row
