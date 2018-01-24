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

redmine_instance = redmine.Redmine(redmine_url, username=redmine_username,
                               password=redmine_password)

user_id = redmine_instance.user.get('current').id
statuses = redmine_instance.issue_status.all()
projects = redmine_instance.project.all()

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

# transform list of dicts format
# {'Remote': '0'} -> {'name': 'Remote', 'value': '0'}
# this is an inclusive filter
filtered_custom_fields = list()
for custom_field in config['custom_field_filter']:
    for key in custom_field.keys():
        filtered_custom_fields.append({'name': key, 'value': custom_field[key]})

# get sorted list of issues
issues = sorted(redmine_instance.issue.filter(assigned_to_id=user_id,
                                          status_id=status_id_filter_str),
                key=lambda issue: issue.priority['id'],
                reverse=True)

for issue in issues:
    project_id = issue.project['id']

    if project_id not in filtered_projects:
        if hasattr(issue, 'custom_fields'):
            # convert redmine.resources.CustomField object list to list of dicts
            issue_custom_fields = list()
            for custom_field in issue.custom_fields:
                issue_custom_fields.append({'name': custom_field['name'],
                                            'value': custom_field['value']})

            for custom_field in filtered_custom_fields:
                if custom_field in issue_custom_fields:
                    message = build_message(issue)
                    send_message(message['title'], message['body'],
                                 message['urgency'])
                    continue
        #else:
        #    message = build_message(issue)
        #    send_message(message['title'], message['body'],
        #                 message['urgency'])
