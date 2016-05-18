import smtplib
from email.mime.text import MIMEText
from statemanager.statemanager_domain import WorkflowDefinition, StateHistory


def _create_notification(subject: str, content: str, to: [str], cc: [str]) -> MIMEText:
    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['To'] = to
    msg['Cc'] = cc
    msg['From'] = 'noreply@workflow.com'
    return msg


def _send_notification(msg: MIMEText, to: [str], cc: [str], smtp_host: str) -> bool:
    smtp = smtplib.SMTP(str)
    smtp.sendmail('noreply@workflow.com', to, msg.as_string())


def notify_to_next_state(workflow_definition: WorkflowDefinition, current_state: StateHistory, users: [str]) -> bool:
    pass


def notify_to_previous_state(workflow_definition: WorkflowDefinition, current_state: StateHistory,
                             users: [str]) -> bool:
    pass
