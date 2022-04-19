''' Sender '''
# pylint: disable=too-few-public-methods
from jinja2.sandbox import SandboxedEnvironment
from pymongo.collection import ReturnDocument

import setting
from models.senderdb import (SenderCampaignDB, SenderLogsDB, SenderReceiverDB,
                             SenderSESLogsDB)
from module.awsses import AWSSES
from module.team import Team
from module.users import User


class SenderCampaign:
    ''' SenderCampaign class '''

    @staticmethod
    def create(name, pid, tid, uid):
        ''' Create new campaign

        :param str name: campaign name
        :param str pid: pid
        :param str tid: tid
        :param str uid: uid

        '''

        data = SenderCampaignDB.new(
            name=name.strip(), pid=pid, tid=tid, uid=uid)
        return SenderCampaignDB().add(data)

    @staticmethod
    def get(cid, pid=None, tid=None):
        ''' Get campaign

        :param str cid: cid
        :param str pid: pid
        :param str tid: tid

        '''
        query = {'_id': cid}

        if pid is not None:
            query['created.pid'] = pid

        if tid is not None:
            query['created.tid'] = tid

        return SenderCampaignDB().find_one(query)

    @staticmethod
    def get_list(pid, tid):
        ''' Get list campaign

        :param str pid: pid
        :param str tid: tid

        '''
        return SenderCampaignDB().find({'created.pid': pid, 'created.tid': tid})

    @staticmethod
    def save_mail(cid, subject, content, preheader, layout):
        ''' Save mail data

        :param str cid: cid
        :param str subject: subject
        :param str content: content
        :param str preheader: preheader
        :param str layout: layout

        '''
        return SenderCampaignDB().find_one_and_update(
            {'_id': cid},
            {'$set': {
                'mail.subject': subject,
                'mail.content': content,
                'mail.preheader': preheader,
                'mail.layout': layout,
            }},
            return_document=ReturnDocument.AFTER,
        )

    @staticmethod
    def save_receiver(cid, teams, team_w_tags, users=None, all_users=False):
        ''' Save receiver

        :param str cid: cid
        :param list teams: teams
        :param list team_w_tags: {'team': [tag, ...]}
        :param list users: users
        :param bool all_users: all volunteer users

        .. note:: ``users`` not in completed implement

        '''
        update = {'receiver.teams': teams}
        update['receiver.users'] = users if users else []
        update['receiver.all_users'] = all_users
        update['receiver.team_w_tags'] = team_w_tags

        return SenderCampaignDB().find_one_and_update(
            {'_id': cid},
            {'$set': update},
            return_document=ReturnDocument.AFTER,
        )


class SenderMailer:
    ''' Sender Mailer

    :param str template_path: template path
    :param str subject: subject
    :param dict source: {'name': str, 'mail': str}

    '''

    def __init__(self, template_path, subject, content, source=None):
        with open(template_path, 'r', encoding='UTF8') as files:
            body = SandboxedEnvironment().from_string(files.read()).render(**content)

            self.tpl = SandboxedEnvironment().from_string(body)
            self.subject = SandboxedEnvironment().from_string(subject)

            if source is None:
                source = setting.AWS_SES_FROM

            self.awsses = AWSSES(aws_access_key_id=setting.AWS_ID,
                                 aws_secret_access_key=setting.AWS_KEY, source=source)

    def send(self, to_list, data, x_coscup=None):
        ''' Send mail

        :param list to_list: [{'name': str, 'mail': str}, ]
        :param dict data: data for render

        '''
        raw_mail = self.awsses.raw_mail(
            to_addresses=to_list,
            subject=self.subject.render(**data),
            body=self.tpl.render(**data),
            x_coscup=x_coscup,
        )
        return self.awsses.send_raw_email(data=raw_mail)


class SenderMailerVolunteer(SenderMailer):
    ''' Sender using volunteer template '''

    def __init__(self, subject, content, source=None):
        super().__init__(
            template_path='/app/templates/mail/sender_base.html',
            subject=subject, content=content, source=source)


class SenderMailerCOSCUP(SenderMailer):
    ''' Sender using COSCUP template '''

    def __init__(self, subject, content, source=None):
        super().__init__(
            template_path='/app/templates/mail/coscup_base.html',
            subject=subject, content=content, source=source)


class SenderLogs:
    ''' SenderLogs object '''

    @staticmethod
    def save(cid, layout, desc, receivers):
        ''' save log

        :param str cid: cid
        :param str layout: layout
        :param str desc: desc
        :param list receivers: receivers

        '''
        SenderLogsDB().add(cid=cid, layout=layout, desc=desc, receivers=receivers)

    @staticmethod
    def get(cid):
        ''' Get log

        :param str cid: cid

        '''
        for raw in SenderLogsDB().find({'cid': cid}, sort=(('_id', -1), )):
            yield raw


class SenderSESLogs:
    ''' SenderSESLogs '''

    @staticmethod
    def save(cid, name, mail, result):
        ''' Save log

        :param str cid: cid
        :param str name: name
        :param str mail: mail
        :param dict result: result

        '''
        SenderSESLogsDB().add(cid=cid, mail=mail, name=name, ses_result=result)


class SenderReceiver:
    ''' SenderReceiver object '''

    @staticmethod
    def replace(pid, cid, datas):
        ''' Replace

        :param str pid: pid
        :param str cid: cid
        :param list datas: list of dict data

        '''
        sender_receiver_db = SenderReceiverDB()
        sender_receiver_db.remove_past(pid=pid, cid=cid)

        uids = []
        for data in datas:
            if 'uid' in data and data['uid']:
                uids.append(data['uid'])

        user_infos = User.get_info(uids=uids)
        user_info_uids = {}
        for uid, data in user_infos.items():
            user_info_uids[uid] = {
                'name': data['profile']['badge_name'],
                'mail': data['oauth']['email'],
            }

        save_datas = []
        for data in datas:
            if 'uid' in data and data['uid'] and data['uid'] in user_info_uids:
                _data = SenderReceiverDB.new(pid=pid, cid=cid,
                                             name=user_info_uids[data['uid']
                                                                 ]['name'],
                                             mail=user_info_uids[data['uid']
                                                                 ]['mail'],
                                             )
            else:
                _data = SenderReceiverDB.new(
                    pid=pid, cid=cid, name=data['name'], mail=data['mail'])

            _data['data'].update(data)
            save_datas.append(_data)

        sender_receiver_db.update_data(pid=pid, cid=cid, datas=save_datas)

    @staticmethod
    def update(pid, cid, datas):
        ''' Update

        :param str pid: pid
        :param str cid: cid
        :param list datas: list of dict data

        '''
        uids = []
        for data in datas:
            if 'uid' in data and data['uid']:
                uids.append(data['uid'])

        user_infos = User.get_info(uids=uids)
        user_info_uids = {}
        for uid, data in user_infos.items():
            user_info_uids[uid] = {
                'name': data['profile']['badge_name'],
                'mail': data['oauth']['email'],
            }

        save_datas = []
        for data in datas:
            if 'uid' in data and data['uid'] and data['uid'] in user_info_uids:
                _data = SenderReceiverDB.new(pid=pid, cid=cid,
                                             name=user_info_uids[data['uid']
                                                                 ]['name'],
                                             mail=user_info_uids[data['uid']
                                                                 ]['mail'],
                                             )
            else:
                _data = SenderReceiverDB.new(
                    pid=pid, cid=cid, name=data['name'], mail=data['mail'])

            _data['data'].update(data)
            save_datas.append(_data)

        SenderReceiverDB().update_data(pid=pid, cid=cid, datas=save_datas)

    @staticmethod
    def remove(pid, cid):
        ''' Update

        :param str pid: pid
        :param str cid: cid

        '''
        SenderReceiverDB().remove_past(pid=pid, cid=cid)

    @staticmethod
    def get(pid, cid):
        ''' Get

        :param str pid: pid
        :param str cid: cid

        :return: fields, raws

        '''
        datas = list(SenderReceiverDB().find({'pid': pid, 'cid': cid}))
        fields = ['name', 'mail']
        for data in datas:
            for k in data['data']:
                if k not in ('name', 'mail') and k not in fields:
                    fields.append(k)

        raws = []
        for data in datas:
            raw = []
            for field in fields:
                raw.append(data['data'].get(field, ''))

            raws.append(raw)

        return fields, raws

    @staticmethod
    def get_from_user(pid, tids):
        ''' Get users from userdb by project, team

        :param str pid: pid
        :param str tids: team id or ids

        :return: fields, raws

        '''
        if isinstance(tids, str):
            tids = (tids, )

        team_users = Team.get_users(pid=pid, tids=tids)
        uids = []
        for user_ids in team_users.values():
            uids.extend(user_ids)

        user_infos = User.get_info(uids=uids)
        datas = []
        for value in user_infos.values():
            # append, plus more data here in the future
            datas.append({
                'name': value['profile']['badge_name'],
                'mail': value['oauth']['email'],
            })

        raws = []
        for data in datas:
            raw = []
            for field in ('name', 'mail'):
                raw.append(data[field])

            raws.append(raw)

        return (('name', 'mail'), raws)

    @staticmethod
    def get_all_users():
        ''' Get all users '''
        uids = []
        for user in User.get_all_users():
            uids.append(user['_id'])

        user_infos = User.get_info(uids=uids)
        raws = []
        for value in user_infos.values():
            raws.append((
                value['profile']['badge_name'],
                value['oauth']['email'],
            ))

        return (('name', 'mail'), raws)

    @staticmethod
    def get_by_tags(pid, tid, tags):
        ''' Get users by tags '''
        uids = Team.get_members_uid_by_tags(pid=pid, tid=tid, tags=tags)

        user_infos = User.get_info(uids=uids)
        raws = []
        for value in user_infos.values():
            raws.append((
                value['profile']['badge_name'],
                value['oauth']['email'],
            ))

        return (('name', 'mail'), raws)
