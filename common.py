from flask import session


def get_current_team(db):
    if 'team' in session:
        return get_team(db, session['team'])
    return None


def get_team(db, username, password=None):
    db_team = db.teams.find_one({'name': username})
    if not db_team:
        return None
    if not password or db_team['password'] == password:
        return db_team
    return None
