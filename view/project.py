import csv
import io
import math

import arrow
from flask import Blueprint
from flask import g
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from models.oauth_db import OAuthDB
from models.users_db import UsersDB
from module.form import Form
from module.project import Project
from module.team import Team
from module.users import User


VIEW_PROJECT = Blueprint('project', __name__, url_prefix='/project')


@VIEW_PROJECT.route('/')
def index():
    projects = []
    data = list(Project.all())
    for d in data:
        date = arrow.get(d['action_date'])
        d['action_date_str'] = '%s (%s)' % (date.format('YYYY-MM-DD'), date.humanize(arrow.now()))

    per = 3
    for i in range(int(math.ceil(len(data) / float(per)))):
        projects.append(data[per*i:min([per*(i+1), len(data)])])

    return render_template('./project_index.html', projects=projects)

@VIEW_PROJECT.route('/<pid>/edit', methods=('GET', 'POST'))
def project_edit(pid):
    project = Project.get(pid)
    if g.user['account']['_id'] not in project['owners']:
        return redirect(url_for('project.team_page', pid=pid, _scheme='https', _external=True))

    if request.method == 'GET':
        if 'volunteer_certificate_hours' not in project:
            project['volunteer_certificate_hours'] = 0

        return render_template('./project_edit.html', project=project)

    elif request.method == 'POST':
        data = {
            'desc': request.form['desc'].strip(),
            'name': request.form['name'].strip(),
            'volunteer_certificate_hours': max([0, int(request.form['volunteer_certificate_hours'])]),
            'calendar': request.form['calendar'].strip(),
            'mailling_staff': request.form['mailling_staff'].strip(),
            'mailling_leader': request.form['mailling_leader'].strip(),
        }
        Project.update(pid, data)
        return redirect(url_for('project.project_edit', pid=pid, _scheme='https', _external=True))

@VIEW_PROJECT.route('/<pid>/edit/team', methods=('GET', 'POST'))
def project_edit_create_team(pid):
    project = Project.get(pid)
    if g.user['account']['_id'] not in project['owners']:
        return redirect(url_for('project.team_page', pid=pid, _scheme='https', _external=True))

    teams = Team.list_by_pid(project['_id'])
    return render_template('./project_edit_create_team.html', project=project, teams=teams)

@VIEW_PROJECT.route('/<pid>/form', methods=('GET', 'POST'))
def project_form(pid):
    project = Project.get(pid)
    if g.user['account']['_id'] not in project['owners']:
        return redirect(url_for('project.team_page', pid=pid, _scheme='https', _external=True))

    if request.method == 'GET':
        return render_template('./project_form.html', project=project)

@VIEW_PROJECT.route('/<pid>/form/api', methods=('GET', 'POST'))
def project_form_api(pid):
    project = Project.get(pid)
    if g.user['account']['_id'] not in project['owners']:
        return redirect(url_for('project.team_page', pid=pid, _scheme='https', _external=True))

    if request.method == 'POST':
        data = request.get_json()
        if 'case' not in data:
            return redirect(url_for('project.team_page', pid=pid, _scheme='https', _external=True))

        if data['case'] == 'volunteer_certificate':
            fieldnames = ('uid', 'picture', 'value', 'name', 'roc_id', 'birthday', 'company')
            with io.StringIO() as str_io:
                csv_writer = csv.DictWriter(str_io, fieldnames=fieldnames)
                csv_writer.writeheader()

                for raw in Form.all_volunteer_certificate(pid):
                    user_info = UsersDB().find_one({'_id': raw['uid']})
                    oauth = OAuthDB().find_one({'owner': raw['uid']}, {'data.picture': 1})

                    data = {
                        'uid': raw['uid'],
                        'picture': oauth['data']['picture'],
                        'value': raw['data']['value'],
                        'name': user_info['profile_real']['name'],
                        'roc_id': user_info['profile_real']['roc_id'],
                        'birthday': user_info['profile_real']['birthday'],
                        'company': user_info['profile_real']['company'],
                    }

                    csv_writer.writerow(data)

                result = []
                for raw in csv.reader(io.StringIO(str_io.getvalue())):
                    result.append(raw)

                return jsonify({'result': result})

        elif data['case'] == 'traffic_fee':
            fieldnames = ('uid', 'picture', 'apply', 'fee', 'fromwhere', 'howto')
            with io.StringIO() as str_io:
                csv_writer = csv.DictWriter(str_io, fieldnames=fieldnames)
                csv_writer.writeheader()

                for raw in Form.all_traffic_fee(pid):
                    user_info = UsersDB().find_one({'_id': raw['uid']})
                    oauth = OAuthDB().find_one({'owner': raw['uid']}, {'data.picture': 1})

                    data = {
                        'uid': raw['uid'],
                        'picture': oauth['data']['picture'],
                        'apply': raw['data']['apply'],
                        'fee': raw['data']['fee'],
                        'fromwhere': raw['data']['fromwhere'],
                        'howto': raw['data']['howto'],
                    }

                    csv_writer.writerow(data)

                result = []
                for raw in csv.reader(io.StringIO(str_io.getvalue())):
                    result.append(raw)

                return jsonify({'result': result})

        elif data['case'] == 'accommodation':
            fieldnames = ('uid', 'picture', 'key', 'status')
            with io.StringIO() as str_io:
                csv_writer = csv.DictWriter(str_io, fieldnames=fieldnames)
                csv_writer.writeheader()

                for raw in Form.all_accommodation(pid):
                    user_info = UsersDB().find_one({'_id': raw['uid']})
                    oauth = OAuthDB().find_one({'owner': raw['uid']}, {'data.picture': 1})

                    data = {
                        'uid': raw['uid'],
                        'picture': oauth['data']['picture'],
                        'key': raw['data']['key'],
                        'status': raw['data']['status'],
                    }

                    csv_writer.writerow(data)

                result = []
                for raw in csv.reader(io.StringIO(str_io.getvalue())):
                    result.append(raw)

                return jsonify({'result': result})

        elif data['case'] == 'appreciation':
            fieldnames = ('uid', 'picture', 'available', 'key', 'value')
            with io.StringIO() as str_io:
                csv_writer = csv.DictWriter(str_io, fieldnames=fieldnames)
                csv_writer.writeheader()

                for raw in Form.all_appreciation(pid):
                    user_info = UsersDB().find_one({'_id': raw['uid']})
                    oauth = OAuthDB().find_one({'owner': raw['uid']}, {'data.picture': 1})

                    data = {
                        'uid': raw['uid'],
                        'picture': oauth['data']['picture'],
                        'available': raw['data']['available'],
                        'key': raw['data']['key'],
                        'value': raw['data']['value'],
                    }
                    csv_writer.writerow(data)

                result = []
                for raw in csv.reader(io.StringIO(str_io.getvalue())):
                    result.append(raw)

                return jsonify({'result': result})

@VIEW_PROJECT.route('/<pid>/edit/team/api', methods=('GET', 'POST'))
def project_edit_create_team_api(pid):
    project = Project.get(pid)
    if g.user['account']['_id'] not in project['owners']:
        return redirect(url_for('project.team_page', pid=pid, _scheme='https', _external=True))

    if request.method == 'GET':
        _team = Team.get(pid, request.args['tid'].strip())
        team = {}
        for k in ('name', 'chiefs', 'members', 'owners', 'tid', 'headcount', 'mailling'):
            if k in _team:
                team[k] = _team[k]

        if 'headcount' not in team:
            team['headcount'] = 0
        else:
            team['headcount'] = max([0, int(team['headcount'])])

        return jsonify(team)

    elif request.method == 'POST':
        data = request.json
        if data['submittype'] == 'update':
            Team.update_setting(pid=pid, tid=data['tid'], data=data)
            return u'%s' % data
        elif data['submittype'] == 'create':
            Team.create(pid=pid, tid=data['tid'], name=data['name'], owners=project['owners'])
            return u'%s' % data

@VIEW_PROJECT.route('/<pid>/')
def team_page(pid):
    teams = []
    project = Project.get(pid)
    if not project:
        return u'no data', 404

    data = list(Team.list_by_pid(project['_id']))
    uids = []
    for t in data:
        uids.extend(t['chiefs'])

    user_info = User.get_info(uids)
    for t in data:
        t['chiefs_name'] = []
        for uid in t['chiefs']:
            t['chiefs_name'].append(user_info[uid]['profile']['badge_name'])

    # ----- group for layout ----- #
    per = 3
    for i in range(int(math.ceil(len(data) / float(per)))):
        teams.append(data[per*i:min([per*(i+1), len(data)])])

    editable = g.user['account']['_id'] in project['owners']

    return render_template('./project_teams_index.html',
        teams=teams,
        project=project,
        editable=editable,
    )
