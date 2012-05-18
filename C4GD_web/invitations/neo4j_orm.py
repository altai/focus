import MySQLdb

conn = MySQLdb.connect(host="localhost", user="root", passwd="8903324", db="invitations")
cursor = conn.cursor()


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

def create_new_user(email, password):
    query = """
        INSERT INTO invitations.users 
        SET email='%s', password='%s';
    """
    cursor.execute(query)
    conn.commit()