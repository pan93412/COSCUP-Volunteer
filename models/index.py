''' Create the collection index

This file is executed to create the index in MongoDB. All models
with `index()` will be aggregated here.

'''
from models.budgetdb import BudgetDB
from models.expensedb import ExpenseDB
from models.formdb import FormDB
from models.mailletterdb import MailLetterDB
from models.mattermost_link_db import MattermostLinkDB
from models.mattermostdb import MattermostUsersDB
from models.oauth_db import OAuthDB
from models.projectdb import ProjectDB
from models.senderdb import SenderReceiverDB
from models.teamdb import (TeamDB, TeamMemberChangedDB, TeamMemberTagsDB,
                           TeamPlanDB)
from models.telegram_db import TelegramDB
from models.users_db import UsersDB
from models.usessiondb import USessionDB
from models.waitlistdb import WaitListDB


def make_index() -> None:
    ''' Make index for the collection with `index()` '''
    BudgetDB().index()
    ExpenseDB().index()
    FormDB().index()
    MailLetterDB().index()
    MattermostLinkDB().index()
    MattermostUsersDB().index()
    OAuthDB().index()
    ProjectDB(pid='').index()
    SenderReceiverDB().index()
    TeamDB(pid='', tid='').index()
    TeamMemberChangedDB().index()
    TeamMemberTagsDB().index()
    TeamPlanDB().index()
    TelegramDB().index()
    USessionDB().index()
    UsersDB().index()
    WaitListDB().index()


if __name__ == '__main__':
    make_index()
