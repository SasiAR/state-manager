import smtplib
from email.mime.text import MIMEText
from statemanager.statemanager_domain import WorkflowDefinition, StateHistory, StateDefinition
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


def _send_notification(msg: MIMEText, to: [str], cc: [str]) -> bool:
    smtp = smtplib.SMTP(__statemanager_smtphost)
    # smtp.sendmail('noreply@workflow.com', to, msg.as_string())


def notify_users(workflow_type: str, rec_id: str) -> bool:
    workflow_definition = current_session().query(WorkflowDefinition).filter(
        WorkflowDefinition.workflow_type == workflow_type).first()

    if workflow_definition.email_notification.lower() == 'n':
        return

    current_state = current_session().query(StateHistory, StateDefinition).filter(and_(
        and_(StateHistory.rec_id == rec_id, StateDefinition.workflow_id == workflow_definition.workflow_id),
        StateHistory.state_id == StateDefinition.state_id)).order_by(
        desc(StateHistory.insert_ts)).first()

    cc_users = current_session().query(StateHistory.user_subscription_notification).filter(
        and_(StateHistory.rec_id == rec_id), StateHistory.user_subscription_notification != None).all()

    to_users = workflow_definition.email_to.split(";")
    subject = workflow_definition.email_subject + "-" + rec_id
    content = workflow_definition.email_content
    content += " The state was changed with notes - "
    content += current_state.StateHistory.notes

    msg = _create_notification(subject=subject, content=content, to=to_users, cc=cc_users)
    _send_notification(msg=msg, to=to_users, cc=cc_users)
