from __future__ import absolute_import
from __future__ import unicode_literals

from bson.objectid import ObjectId
from celery.utils.log import get_task_logger
from jinja2 import Environment
from jinja2 import FileSystemLoader

import setting
from celery_task.celery import app
from models.teamdb import TeamMemberChangedDB
from module.awsses import AWSSES
from module.project import Project
from module.team import Team
from module.users import User

logger = get_task_logger(__name__)


@app.task(bind=True, name='mail.sys.test',
    autoretry_for=(Exception, ), retry_backoff=True, max_retries=5,
    routing_key='cs.mail.sys.test', exchange='COSCUP-SECRETARY')
def mail_sys_test(sender, **kwargs):
    logger.info('!!! [%s]' % kwargs)
    raise Exception('Test in error and send mail.')


@app.task(bind=True, name='mail.sys.weberror',
    autoretry_for=(Exception, ), retry_backoff=True, max_retries=5,
    routing_key='cs.mail.sys.weberror', exchange='COSCUP-SECRETARY')
def mail_sys_weberror(sender, **kwargs):
    ses = AWSSES(setting.AWS_ID, setting.AWS_KEY, setting.AWS_SES_FROM)

    raw_mail = ses.raw_mail(
        to_addresses=[setting.ADMIN_To, ],
        subject='[COSCUP-SECRETARY] %s' % kwargs['title'],
        body=kwargs['body'],
    )

    ses.send_raw_email(data=raw_mail)


@app.task(bind=True, name='mail.member.waiting',
    autoretry_for=(Exception, ), retry_backoff=True, max_retries=5,
    routing_key='cs.mail.member.waiting', exchange='COSCUP-SECRETARY')
def mail_member_waiting(sender, **kwargs):
    TPLENV = Environment(loader=FileSystemLoader('./templates/mail'))
    template = TPLENV.get_template('./base_member_waiting.html')

    team_member_change_db = TeamMemberChangedDB()
    awsses = AWSSES(
            aws_access_key_id=setting.AWS_ID,
            aws_secret_access_key=setting.AWS_KEY,
            source=setting.AWS_SES_FROM)

    for raw in team_member_change_db.find(
        {'done.mail': {'$exists': False}, 'case': 'waiting'},
        sort=(('create_at', 1), )):
        team = Team.get(raw['pid'], raw['tid'])

        uids = []
        uids.extend(team['chiefs'])
        uids.append(raw['uid'])

        users = User.get_info(uids=uids)

        for uid in team['chiefs']:
            body = template.render(
                    name=users[uid]['profile']['badge_name'],
                    uid=raw['uid'],
                    apply_name=users[raw['uid']]['profile']['badge_name'],
                    team_name=team['name'], pid=team['pid'], tid=team['tid'], )

            raw_mail = awsses.raw_mail(
                    to_addresses=(dict(name=users[uid]['profile']['badge_name'], mail=users[uid]['oauth']['email']), ),
                    subject=u'申請加入通知信 - %s' % users[raw['uid']]['profile']['badge_name'],
                    body=body,
                )

            r = mail_member_send.apply_async(kwargs={'raw_mail': raw_mail.as_string(), 'rid': str(raw['_id'])})
            logger.info(r)


@app.task(bind=True, name='mail.member.deny',
    autoretry_for=(Exception, ), retry_backoff=True, max_retries=5,
    routing_key='cs.mail.member.deny', exchange='COSCUP-SECRETARY')
def mail_member_deny(sender, **kwargs):
    TPLENV = Environment(loader=FileSystemLoader('./templates/mail'))
    template = TPLENV.get_template('./base_member_deny.html')

    team_member_change_db = TeamMemberChangedDB()
    awsses = AWSSES(
            aws_access_key_id=setting.AWS_ID,
            aws_secret_access_key=setting.AWS_KEY,
            source=setting.AWS_SES_FROM)

    for raw in team_member_change_db.find(
        {'done.mail': {'$exists': False}, 'case': 'deny'},
        sort=(('create_at', 1), )):
        team = Team.get(raw['pid'], raw['tid'])
        project = Project().get(pid=team['pid'])

        user = User.get_info(uids=(raw['uid'], ))[raw['uid']]
        body = template.render(
                name=user['profile']['badge_name'],
                team_name=team['name'],
                project_name=project['name'],
                pid=team['pid'], )

        raw_mail = awsses.raw_mail(
                to_addresses=(dict(name=user['profile']['badge_name'], mail=user['oauth']['email']), ),
                subject=u'申請加入 %s 未核准' % team['name'],
                body=body,
            )

        r = mail_member_send.apply_async(kwargs={'raw_mail': raw_mail.as_string(), 'rid': str(raw['_id'])})
        logger.info(r)


@app.task(bind=True, name='mail.member.add',
    autoretry_for=(Exception, ), retry_backoff=True, max_retries=5,
    routing_key='cs.mail.member.add', exchange='COSCUP-SECRETARY')
def mail_member_add(sender, **kwargs):
    TPLENV = Environment(loader=FileSystemLoader('./templates/mail'))
    template = TPLENV.get_template('./base_member_add.html')

    team_member_change_db = TeamMemberChangedDB()
    awsses = AWSSES(
            aws_access_key_id=setting.AWS_ID,
            aws_secret_access_key=setting.AWS_KEY,
            source=setting.AWS_SES_FROM)

    for raw in team_member_change_db.find(
        {'done.mail': {'$exists': False}, 'case': 'add'},
        sort=(('create_at', 1), )):
        team = Team.get(raw['pid'], raw['tid'])

        user = User.get_info(uids=(raw['uid'], ))[raw['uid']]

        body = template.render(
                name=user['profile']['badge_name'],
                team_name=team['name'], pid=team['pid'], tid=team['tid'], )

        raw_mail = awsses.raw_mail(
                to_addresses=(dict(name=user['profile']['badge_name'], mail=user['oauth']['email']), ),
                subject=u'申請加入 %s 核准' % team['name'],
                body=body,
            )

        r = mail_member_send.apply_async(kwargs={'raw_mail': raw_mail.as_string(), 'rid': str(raw['_id'])})
        logger.info(r)


@app.task(bind=True, name='mail.member.del',
    autoretry_for=(Exception, ), retry_backoff=True, max_retries=5,
    routing_key='cs.mail.member.del', exchange='COSCUP-SECRETARY')
def mail_member_del(sender, **kwargs):
    TPLENV = Environment(loader=FileSystemLoader('./templates/mail'))
    template = TPLENV.get_template('./base_member_del.html')

    team_member_change_db = TeamMemberChangedDB()
    awsses = AWSSES(
            aws_access_key_id=setting.AWS_ID,
            aws_secret_access_key=setting.AWS_KEY,
            source=setting.AWS_SES_FROM)

    for raw in team_member_change_db.find(
        {'done.mail': {'$exists': False}, 'case': 'del'},
        sort=(('create_at', 1), )):
        team = Team.get(raw['pid'], raw['tid'])

        user = User.get_info(uids=(raw['uid'], ))[raw['uid']]

        body = template.render(
                name=user['profile']['badge_name'],
                team_name=team['name'], )

        raw_mail = awsses.raw_mail(
                to_addresses=(dict(name=user['profile']['badge_name'], mail=user['oauth']['email']), ),
                subject=u'您已被移除 %s 的組員資格！' % team['name'],
                body=body,
            )

        r = mail_member_send.apply_async(kwargs={'raw_mail': raw_mail.as_string(), 'rid': str(raw['_id'])})
        logger.info(r)


@app.task(bind=True, name='mail.member.send',
    autoretry_for=(Exception, ), retry_backoff=True, max_retries=5,
    routing_key='cs.mail.member.send', exchange='COSCUP-SECRETARY')
def mail_member_send(sender, **kwargs):
    team_member_change_db = TeamMemberChangedDB()
    awsses = AWSSES(
            aws_access_key_id=setting.AWS_ID,
            aws_secret_access_key=setting.AWS_KEY,
            source=setting.AWS_SES_FROM)

    resp = awsses.send_raw_email(data_str=kwargs['raw_mail'])
    logger.info(resp)
    if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception('HTTPStatusCode not `200`, do retry')

    team_member_change_db.find_one_and_update({'_id': ObjectId(kwargs['rid'])}, {'$set': {'done.mail': True}})
