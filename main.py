from datetime import timedelta
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, session, abort, flash, Response
from pymongo import MongoClient
from admin import admin
from common import *
import time
import threading

app = Flask(__name__)
app.register_blueprint(admin, url_prefix='/admin')
config_lock = threading.Lock()

db = MongoClient().ctf


def log(line):
    line = time.strftime("%H:%M:%S - ") + request.remote_addr + ' - ' + line.encode('utf8') + '\r\n'
    open('log.log', 'ab').write(line)


def is_logged_in():
    return 'team' in session and session['team']


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if is_logged_in():
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrapper


@app.route('/')
def index():
    if is_logged_in():
        return redirect(url_for('private'))
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = request.form['username']
        user_team = get_team(db, user, request.form['password'])
        if user_team:
            session['team'] = user_team['name']
            return redirect(url_for('private'))
        error = 'Invalid Credentials'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    if 'team' in session:
        session.pop('team')
    return redirect(url_for('index'))


@app.route('/private/')
@login_required
def private():
    return render_template('private/index.html', team=get_current_team(db))


@app.route('/private/scoreboard')
@login_required
def scoreboard():
    return render_template('private/scoreboard.html', teams=list(db.teams.find()))


@app.route('/private/challenges')
@login_required
def challenges():
    return render_template('private/challenges.html', team=get_current_team(db), challenges=list(db.challenges.find()))


@app.route('/private/challenges/<challenge>', methods=['GET', 'POST'])
@login_required
def challenge(challenge):
    db_chal = db.challenges.find_one({'name': challenge})
    if not db_chal:
        return abort(404)

    team = get_current_team(db)
    bad_flag = False
    if request.method == 'POST':
        flag = request.form['flag']
        if flag == db_chal['flag']:
            db.teams.update_one({'name': session['team']}, {'$addToSet': {'solved': challenge}})
            if challenge not in team['solved']:
                log('Team "{0}" solved challenge "{1}"'.format(session['team'], challenge))
                flash('Successfully solved {0}'.format(challenge))
            else:
                log('Team "{0}" resubmitted challenge "{1}"'.format(session['team'], challenge))
                flash('Flag "{0}" resubmitted'.format(challenge))

            return redirect(url_for('challenges'))
        log('Team "{0}" entered wrong flag "{1}" for challenge "{2}"'.format(session['team'], flag, challenge))
        bad_flag = True

    return render_template('private/challenge.html', team=team, challenge=db_chal, bad_flag=bad_flag)


@app.before_first_request
def set_cookie_time_limit():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=2)


@app.before_request
def refresh_session():
    session.modified = True


# Exposed functions
def did_team_solve(team, challenge):
    print team
    for solved in team['solved']:
        if solved == challenge['name']:
            return True
    return False


def compute_score(team):
    score = 0
    for chal in team['solved']:
        chal = db.challenges.find_one({'name': chal})
        score += chal['points']
    return score


def sort_by_score(teams):
    return sorted(teams, key=lambda team: compute_score(team), cmp=lambda s1, s2: s2 - s1)


def compare_challenges(c1, c2):
    if c1['category'] != c2['category']:
        return -1 if c1['category'] < c2['category'] else 1
    return c1['points'] - c2['points']


def sort_challenges(challenges):
    return sorted(challenges, cmp=compare_challenges)


def teams_that_solved(challenge):
    result = db.teams.aggregate([
        {
            '$unwind': '$solved'
        },
        {
            '$match': {
                'solved': challenge
            }
        }
    ])

    return [team['name'] for team in result]


app.jinja_env.globals.update(did_team_solve=did_team_solve)
app.jinja_env.globals.update(compute_score=compute_score)
app.jinja_env.globals.update(sort_by_score=sort_by_score)
app.jinja_env.globals.update(sort_challenges=sort_challenges)
app.jinja_env.globals.update(teams_that_solved=teams_that_solved)


app.secret_key = '\xbd\x12\x92]\xd6\xfaC\xafy\x8a\x82\x00Y\xd2\xbc=\x9dQ\xe106??\x86'

if __name__ == '__main__':
    # FIXME: debug=False
    app.run(host='0.0.0.0', debug=True, port=80, threaded=True)
