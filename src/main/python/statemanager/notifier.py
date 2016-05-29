import smtplib
from email.mime.text import MIMEText
from statemanager.domain import WorkflowDefinition, StateHistory, StateDefinition
from statemanager.statemanager import current_session
from sqlalchemy import and_, desc

__statemanager_smtphost = None


def set_smtphost(host: str) -> None:
    global __statemanager_smtphost
    __statemanager_smtphost = host


def _create_notification(subject: str, content: str, to: [str], cc: [str]) -> MIMEText:
    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['To'] = to
    msg['Cc'] = cc
    msg['From'] = 'noreply@workflow.com'
    return msg


def _send_notification(msg: MIMEText) -> bool:
    smtp = smtplib.SMTP(__statemanager_smtphost)
    smtp.send_message(msg)


def notify_users(workflow_type: str, item_type: str, item_id: str) -> bool:
    workflow_definition = current_session().query(WorkflowDefinition).filter(
        WorkflowDefinition.workflow_type == workflow_type).first()

    if workflow_definition.email_notification.lower() == 'n':
        return False

    current_state = current_session().query(StateHistory, StateDefinition).filter(and_(and_(
        and_(StateHistory.item_id == item_id, StateDefinition.workflow_id == workflow_definition.workflow_id),
        StateHistory.state_id == StateDefinition.state_id), StateHistory.item_type == item_type)).order_by(
        desc(StateHistory.insert_ts)).first()

    subscription = current_session().query(StateHistory.user_subscription_notification).filter(and_(
        and_(StateHistory.item_id == item_id, StateHistory.user_subscription_notification != None),
        StateHistory.item_type == item_type)).all()

    cc_users = []

    if subscription:
        for user in subscription:
            if user[0] not in cc_users:
                cc_users.append(user[0])

    if current_state.StateDefinition.email_to is not None:
        to_users = current_state.StateDefinition.email_to.split(";")
    else:
        to_users = []

    if not to_users and (cc_users is None or cc_users):
        return False

    subject = workflow_definition.email_subject + "-" + item_id
    content = workflow_definition.email_content
    content += " The state was changed to "
    content += current_state.StateDefinition.state_name
    content += " with notes - "
    content += current_state.StateHistory.notes

    msg = _create_notification(subject=subject, content=content, to=to_users, cc=cc_users)
    _send_notification(msg=msg)

    return True
