# redmine-desktop-notifications
Redmine desktop notifications through Freedesktop notifications system

## Introduction
This is a small script to get Redmine notifications on your desktop

Since this script tries to get all projects from your Redmine instance, it'll only works if the user you use is able to list some or all projects.

## Dependencies
* python3-redmine
* python3-notify2
* python3-yaml

## Configuration
Configuration is defined in a YAML file called redmine.yml. This is an example:
```yaml
url: https://your.domain.net/redmine
username: johndoe
password: *******
status_filter:
    - Cancelled
    - Solved
    - Closed

project_filter:
    - Plan 9
    - Manhattan Project

status_urgency_critical:
    - Blocked
    - Awaiting action

status_urgency_low:
    - New
    - Current
```

## TODO
* Allow user to select projects he wishes to get issues from
* Filtering by custom fields
* Filtering by priority (?)
* ...
