#!/usr/bin/python3

import redmine
import notify2
import yaml
from os import path

def build_notification(issue, statuses_by_importance):
    """ Builds and format the notification """
    notification = { 'title':"", 'body':"", 'urgency':"" }

    notification['title'] = issue.project['name']
    notification['body'] = '#' + str(issue.id) + ': ' + issue.subject + '\n' + '<i><b>' + \
                      issue.priority['name'] + '</b> - ' + issue.status['name'] + '</i>'

    if issue.status['id'] in statuses_by_importance['critical_statuses']:
        notification['urgency']='critical'
    elif issue.status['id'] in statuses_by_importance['unimportant_statuses']:
        notification['urgency']='low'
    else:
        notification['urgency']='normal'

    return notification


def send_notification(notification):
    """ Sends a notification """
    icon_file='redmine.png'

    urgency_level = {'low': 0,
                     'normal': 1,
                     'critical': 2}

    uri = path.join(path.dirname(path.abspath(__file__)),
                       icon_file)

    notify2.init("")
    notice = notify2.Notification(notification['title'], notification['body'], uri)

    notice.set_urgency(urgency_level[notification['urgency']])

    notice.show()
    return


def get_config(config_file):
    """ Reads configuration from YAML file """
    config = yaml.load(open(path.join(path.dirname(path.abspath(__file__)),
                       config_file)))
    return config


def get_filters(config, all_statuses, all_projects):
    """ Returns status, project and custom fields filters """
    filtered_statuses = [status['id'] for status in all_statuses if status['name'] in
                         config['status_filter']]
    status_id_filter_str = '!' + '|'.join(str(status_id) for status_id in filtered_statuses)
    
    # filter by project
    filtered_projects = [project['id'] for project in all_projects if project['name'] in
                         config['project_filter']]
    
    # transform list of dicts format
    # {'Remote': '0'} -> {'name': 'Remote', 'value': '0'}
    # this is an inclusive filter
    included_custom_fields = list()
    for custom_field in config['custom_field_filter']:
        for key in custom_field.keys():
            included_custom_fields.append({'name': key, 'value': custom_field[key]})

    return {'status_id_filter_str': status_id_filter_str,
            'filtered_projects': filtered_projects,
            'included_custom_fields': included_custom_fields}

def get_statuses_by_importance(config, all_statuses):
    """
        Returns statuses classified by importance according to the
        configuration file
    
    """
    critical_statuses = [status['id'] for status in all_statuses if status['name'] in
                         config['status_urgency_critical']]

    unimportant_statuses = [status['id'] for status in all_statuses if status['name'] in
                            config['status_urgency_low']]

    return {'critical_statuses': critical_statuses,
            'unimportant_statuses': unimportant_statuses}

def main():
    config = get_config('redmine.yml')
    
    ## connect to redmine
    redmine_instance = redmine.Redmine(config['url'], username=config['username'],
                                   password=config['password'])
    
    user_id = redmine_instance.user.get('current').id
    all_statuses = redmine_instance.issue_status.all()
    all_projects = redmine_instance.project.all()
    
    filters = get_filters(config, all_statuses, all_projects)
    status_id_filter_str = filters['status_id_filter_str']
    filtered_projects = filters['filtered_projects']
    included_custom_fields = filters['included_custom_fields']
    
    statuses_by_importance = get_statuses_by_importance(config, all_statuses)
    critical_statuses = statuses_by_importance['critical_statuses']
    unimportant_statuses = statuses_by_importance['unimportant_statuses']
    
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
    
                for custom_field in included_custom_fields:
                    if custom_field in issue_custom_fields:
                        notification = build_notification(issue, statuses_by_importance)
                        send_notification(notification)
                        continue
            #else:
            #    notification = build_notification(issue)
            #    send_notification(notification['title'], notification['body'],
            #                 notification['urgency'])

if __name__ == "__main__":
    main()
