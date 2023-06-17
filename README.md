# queue_monitor
Let's ask the robot to stay in the queue instead of you.

## requirements:
To run this script you need the `chromium-browser` installed
`apt install chromium-browser`

This script also uses Yandex Cloud for image parsing.
Therefore, you need a service account in Yandex Cloud with the ai.vision.user role.

Don't forget to install some Python modules.
`pip install -r requirements.txt`

Specify the SUCCESS and NO_LUCK global variables based on your preferences.

## run:
`python3 monitor.py`