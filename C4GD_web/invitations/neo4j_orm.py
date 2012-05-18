import MySQLdb

conn = MySQLdb.connect(host="localhost", user="root", passwd="8903324", db="invitations")
cursor = conn.cursor()

# invitations
def save_invitation(email, hash, complete):
    query = "INSERT INTO invitations.invitations SET "+\
        "email='%s'," % email +\
        "hash='%s'," % hash +\
        "complete=%d;" % (1 if complete else 0)
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
    
    
# users
def create_new_user(email, password):
    query = """
        INSERT INTO invitations.users 
        SET email='%s', password='%s';
    """ % email, password
    cursor.execute(query)
    conn.commit()
    
#masks
def get_masks():
    query = """SELECT email_mask FROM invitations.email_masks;"""
    cursor.execute(query)
    rows = cursor.fetchall()
    return rows