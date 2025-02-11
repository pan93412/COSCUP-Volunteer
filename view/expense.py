''' Expense '''
import csv
import io
from datetime import datetime

from flask import (Blueprint, Response, g, jsonify, redirect, render_template,
                   request)

from module.budget import Budget
from module.expense import Expense
from module.project import Project
from module.users import User

VIEW_EXPENSE = Blueprint('expense', __name__, url_prefix='/expense')


@VIEW_EXPENSE.route('/<pid>', methods=('GET', 'POST'))
def by_project_index(pid):
    ''' Project index '''
    project = Project.get(pid)

    if not project:
        return redirect('/')

    is_admin = Budget.is_admin(pid=pid, uid=g.user['account']['_id'])
    if not is_admin:
        return redirect('/')

    if request.method == 'GET':
        return render_template('./expense.html', project=project, is_admin=is_admin)

    if request.method == 'POST':
        data = request.get_json()

        if data['casename'] == 'get':
            datas = list(Expense.get_all_by_pid(pid=pid))

            buids = set()
            uids = set()
            for expense in datas:
                buids.add(expense['request']['buid'])
                uids.add(expense['create_by'])

            budgets = {}
            if buids:
                for raw in Budget.get(buids=list(buids), pid=pid):
                    budgets[raw['_id']] = raw

            users = {}
            if uids:
                user_datas = User.get_info(uids=list(uids))
                for uid, value in user_datas.items():
                    users[uid] = {
                        'oauth': value['oauth'],
                        'profile': {'badge_name': value['profile']['badge_name']}, }

            return jsonify({'datas': datas, 'budgets': budgets, 'users': users,
                            'status': Expense.status()})

        if data['casename'] == 'update':
            # update invoices
            Expense.update_invoices(
                expense_id=data['data']['_id'], invoices=data['data']['invoices'])
            result = Expense.update_status(
                expense_id=data['data']['_id'], status=data['data']['status'])

            return jsonify({'result': result})

    return jsonify({}), 404


@VIEW_EXPENSE.route('/<pid>/dl', methods=('GET', 'POST'))
def by_project_dl(pid):
    ''' Project download '''
    project = Project.get(pid)

    if not project:
        return redirect('/')

    is_admin = Budget.is_admin(pid=pid, uid=g.user['account']['_id'])
    if not is_admin:
        return redirect('/')

    if request.method == 'GET':
        raws = Expense.dl_format(pid=pid)

        if not raws:
            return '', 204

        with io.StringIO() as files:
            csv_writer = csv.DictWriter(files, fieldnames=list(
                raws[0].keys()), quoting=csv.QUOTE_MINIMAL)
            csv_writer.writeheader()
            csv_writer.writerows(raws)

            filename = f"coscup_expense_{pid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            return Response(
                files.getvalue(),
                mimetype='text/csv',
                headers={'Content-disposition': f'attachment; filename={filename}',
                         'x-filename': filename,
                         })

    return '', 204
