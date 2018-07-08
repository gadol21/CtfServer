from flask import Blueprint, render_template, redirect, url_for, request, session, abort, flash, Response, jsonify
from functools import wraps
from string import ascii_letters
from pymongo import MongoClient
import random
import json
from common import *

db = MongoClient().ctf
admin = Blueprint('admin', __name__)


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        cur_team = get_current_team(db)
        if cur_team and cur_team['is_admin']:
            return func(*args, **kwargs)
        else:
            return abort(401)
    return wrapper


@admin.route('/')
@admin_required
def root():
    return render_template('admin/index.html')


@admin.route('/challenges')
@admin_required
def challenges():
    team_solves = db.teams.aggregate([
        {
            '$unwind': '$solved'
        },
        {
            '$group': {
                '_id': '$solved',
                'teams': {'$push': {'name': '$name'}}
            }
        }
    ])
    team_solves = {item['_id']: item['teams'] for item in team_solves}
    return render_template('admin/challenges.html', challenges=list(db.challenges.find()), team_solves=team_solves)


@admin.route('/challenge/<challenge>')
@admin_required
def challenge(challenge):
    chal = db.challenges.find_one({'name': challenge})
    if not chal:
        return abort(404)
    return render_template('admin/challenge.html', challenge=chal)


@admin.route('/challenge/<challenge>/delete')
@admin_required
def delete_challenge(challenge):
    pass


@admin.route('/teams')
@admin_required
def teams():
    return render_template('admin/teams.html', teams=list(db.teams.find()))


@admin.route('/teams/add')
@admin_required
def add_team():
    new_team_name = ''.join([random.choice(ascii_letters) for _ in xrange(10)])
    db.teams.insert_one({
        'name': new_team_name,
        'password': ''.join([random.choice(ascii_letters) for _ in xrange(10)]),
        'solved': [],
        'is_admin': False
    })
    return redirect(url_for('.team', team=new_team_name))


@admin.route('/teams/<team>/delete', methods=['GET', 'POST'])
@admin_required
def delete_team(team):
    bad_pass = False
    if request.method == 'POST':
        if get_current_team(db)['password'] == request.form['password']:
            db.teams.delete_one({
                'name': team
            })
            return redirect(url_for('.teams'))
        bad_pass = True

    return render_template('admin/delete_team.html', team=team, bad_pass=bad_pass)


@admin.route('/team/<team>', methods=['GET', 'POST'])
@admin_required
def team(team):
    target_team = get_team(db, team)
    if not target_team:
        return abort(404)

    if request.method == 'POST':
        new_team_name = request.form['name']
        new_team_password = request.form['password']
        db.teams.update_one({'name': team}, {'$set': {
            'name': new_team_name,
            'password': new_team_password
        }})
        return redirect(url_for('.teams'))

    return render_template('admin/team.html', team=target_team)


@admin.route('/config')
@admin_required
def config():
    return render_template('admin/config.html')


@admin.route('/config/import', methods=['POST'])
@admin_required
def import_config():
    # Make sure parsing the config succeeds before deleting anything
    conf = json.loads(request.files['config'].stream.read())

    # Drop the existing table
    c = MongoClient()
    c.drop_database('ctf')
    # Table specific indexes
    db.challenges.create_index('name')
    db.teams.create_index('name')
    for table in conf:
        db.get_collection(table).insert_many(conf[table])

    return redirect(url_for('.root'))


@admin.route('/config/export')
@admin_required
def export_config():
    conf = {}
    for table in db.collection_names():
        conf[table] = list(db.get_collection(table).find(projection={'_id': False}))
    response = jsonify(conf)
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = 'attachment; filename=config.json'

    return response
