'''
    Celcat to Google Calendar converter
    
    https://github.com/Egsagon/celcat-bot
'''

import yaml
import utils
import celcat
from datetime import datetime, timedelta

from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar


# Read config
with open('config.yml') as file:
    config = yaml.safe_load(file)

# Connect to Google
calendar = GoogleCalendar(
    credentials_path = 'creds.json'
)

# Connect to Celcat
client = celcat.Client(
    server = config['server'],
    ressource = config['ressource']
)

# Fetch Celcat data
now = datetime.now().replace(hour = 0, minute = 0)

print('Pulling data from Celcat')
data = client.fetch(
    groups = config['groups'],
    start = now,
    end = now + timedelta(**config['distance'])
)

# Delete all future Celcat events
for event in calendar.get_events(
    time_min = now,
    timezone = config['timezone'],
    query = '[CELCAT EVENT]'
):
    print(f'Deleting event {event.id}')
    calendar.delete_event(event)

# Write new events
for event in data:
    print(f'Adding event {event.id}')
    
    calendar.add_event(Event(
        start = event.start,
        end = event.end,
        timezone = config['timezone'],
        summary = f'{event.type} - {"+".join(event.modules or "?")}',
        description = event.text + '\n\n[CELCAT EVENT]',
        color_id = utils.get_color(event.color)
    ))

print('Update complete')

# EOF