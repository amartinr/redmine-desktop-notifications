#!/usr/bin/python3

import redmine
import notify2
import yaml
from os import path

def build_message(issue):
    """ Builds and format the notification message """
    project_name = issue.project['name']
    id = issue.id
    subject = issue.subject
    status_id = issue.status['id']
    status_name = issue.status['name']
    priority = issue.priority['name']

    message = { 'title':"", 'body':"", 'urgency':"" }

    message['title'] = project_name
    message['body'] = '#' + str(id) + ': ' + subject + '\n' + '<i><b>' + \
                      issue.priority['name'] + '</b> - ' + status_name + '</i>'

    if remote == '0':
        if status_id in critical_statuses:
            message['urgency']='critical'
        elif status_id in unimportant_statuses:
            message['urgency']='low'
        else:
            message['urgency']='normal'

    return message


def send_message(title, body, urgency='normal'):
    """ Sends a notification message """
    icon_filename='redmine.png'

    urgency_level = {'low': 0,
                     'normal': 1,
                     'critical': 2}

    uri = path.join(path.dirname(path.abspath(__file__)),
                       icon_filename)

    notify2.init("")
    notice = notify2.Notification(title, body, uri)

    notice.set_urgency(urgency_level[urgency])

    notice.show()
    return

# config
config_filename = 'redmine.yml'
config = yaml.load(open(path.join(path.dirname(path.abspath(__file__)),
                       config_filename)))

redmine_url = config['url']
redmine_username = config['username']
redmine_password = config['password']

redmine_ieca = redmine.Redmine(redmine_url, username=redmine_username,
                               password=redmine_password)

user_id = redmine_ieca.user.get('current').id
statuses = redmine_ieca.issue_status.all()
projects = redmine_ieca.project.all()

# fiter by status
status_filter = config['status_filter']
filtered_statuses = [status['id'] for status in statuses if status['name'] in
                     status_filter]
status_id_filter_str = '!' + '|'.join(str(status_id) for status_id in filtered_statuses)

# filter by project
project_filter = config['project_filter']
filtered_projects = [project['id'] for project in projects if project['name'] in
                     project_filter]
# urgency by status
status_urgency_critical = config['status_urgency_critical']
critical_statuses = [status['id'] for status in statuses if status['name'] in
                     status_urgency_critical]

status_urgency_low = config['status_urgency_low']
unimportant_statuses = [status['id'] for status in statuses if status['name'] in
                     status_urgency_low]


# get sorted list of issues
issues = sorted(redmine_ieca.issue.filter(assigned_to_id=user_id,
                                          status_id=status_id_filter_str),
                key=lambda issue: issue.priority['id'],
                reverse=True)

for issue in issues:
    project_id = issue.project['id']

    if project_id not in filtered_projects:
        if hasattr(issue, 'custom_fields'):
            custom_fields = issue.custom_fields

            if any("Remoto" in field['name'] for field in custom_fields):
                remote = [field['value'] for field in custom_fields if
                          field['name'] == "Remoto"][0]
    
                if remote == '0':
                    message = build_message(issue)
                    send_message(message['title'], message['body'],
                                message['urgency'])
