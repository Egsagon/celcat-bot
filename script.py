import math
import logging
import datetime
import requests

import gcsa.event
import gcsa.google_calendar

# ========== CONFIG ========== #

logging.basicConfig(level = 'INFO')

# Server URL (without trailing slash)
SERVER = ...

# Class groups
GROUPS = [ ... ]

# Weeks ahead to scrape
WEEKS = 3

# Celcat ressource type
TYPE = 103

# Calendar timezone
TIMEZONE = 'Europe/Paris'

# Webhook for calendar updates
WEBHOOK = ...

# Days ahead to check for new events
ADD_CHECK = datetime.timedelta(days = 3)

# ============================ #

google_colors = [
    '#7986CB', '#33B679', '#8E24AA', '#E67C73',
    '#F6BF26', '#F4511E', '#039BE5', '#616161',
    '#3F51B5', '#0B8043', '#D50000'
]

# Signature used to recognize bot events
signature = '(( celcat-bot ))'

notification_map = {
    '+': '+ Added',
    '-': '- Removed',
    '*': '* Modified'
}

def hex_to_rgb(hex_color):
    '''Converts an HEX color to RGB.'''
    
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_color(target: str):
    '''
    Get a Google color ID based on the Celcat HEX color.
    '''
    
    target_rgb = hex_to_rgb(target)
    closest_color = None
    min_distance = float('inf')

    for hex_color in google_colors:
        rgb = hex_to_rgb(hex_color)
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(target_rgb, rgb)))
        if distance < min_distance:
            min_distance = distance
            closest_color = hex_color
    
    return str(google_colors.index(closest_color) + 1)

def parse_date(raw: str) -> datetime.datetime:
    return datetime.datetime.strptime(raw, '%Y-%m-%dT%H:%M:%S')

def create_event_key(event) -> tuple:
    return (event.summary, event.start, event.end)

def repr_event(event: gcsa.event.Event) -> str:
    return f"{event.summary} ({event.start.strftime('%d/%m %H:%M')} - {event.end.strftime('%H:%M')})"

logging.info('Connecting to Google Calendar API')
calendar = gcsa.google_calendar.GoogleCalendar(
    credentials_path = 'creds.json'
)

logging.info('Fetching Celcat calendar')
start = datetime.datetime.now()
end = start + datetime.timedelta(weeks = WEEKS)

response = requests.post(
    url =  SERVER + '/Home/GetCalendarData',
    data = {
        'start': start.strftime('%Y-%m-%d'),
        'end': end.strftime('%Y-%m-%d'),
        'resType': TYPE,
        'calView': 'agendaDay',
        'federationIds': GROUPS,
        'colourScheme': '3'
    }
)

response.raise_for_status()
celcat_events: list[dict[str, str]] = response.json()
logging.info(f'Fetched {len(celcat_events)} Celcat events')

old_events: list[gcsa.event.Event] = []
new_events: list[gcsa.event.Event] = []

# Delete old events
for event in calendar.get_events(
    time_min = start,
    time_max = end,
    timezone = TIMEZONE,
    query = signature
):
    logging.info(f'Deleting event {repr_event(event)}')
    old_events.append(event)
    calendar.delete_event(event)

# Add new events
for data in celcat_events:
    
    # >>> type, salle, nom, groupes
    event_details = data['description'].split('\r\n\r\n<br />\r\n\r\n')
    event_class = event_details[1]
    
    name = ', '.join(data['modules'] or '?')
    
    event = calendar.add_event(gcsa.event.Event(
        start = parse_date(data['start']),
        end = parse_date(data['end']),
        timezone = TIMEZONE,
        summary = f'{data['eventCategory']} {name} [{event_class}]',
        description = data['description'] + signature,
        color_id = get_color(data['backgroundColor'])
    ))
    
    logging.info(f'Added event {repr_event(event)}')
    new_events.append(event)

# Send updates to webhook
if not WEBHOOK: exit()

# Compare event changes
notifications = []
old_event_map = {create_event_key(event): event for event in old_events}
new_event_map = {create_event_key(event): event for event in new_events}

# Find removed events
logging.info('Comparing events')
for event_key, old_event in old_event_map.items():
    if (
        event_key not in new_event_map
        # Make sure event wasn't removed because of day advance
        and old_event.start.replace(tzinfo = None) >= start
    ):
        notifications.append(('-', repr_event(event)))

# Find new/modified events
for event_key, new_event in new_event_map.items():
    
    # Limit add notifications
    if new_event.start.replace(tzinfo = None) > start + ADD_CHECK:
        continue
    
    if event_key not in old_event_map:
        notifications.append(('+', repr_event(new_event)))
    
    # Check for description change
    elif old_event_map[event_key].description != new_event.description:
        notifications.append(('*', repr_event(old_event)))

# Send notifications to webhook
if notifications:
    logging.info(f'Sending {len(notifications)} to webhook')
    requests.post(
        url = WEBHOOK,
        json = {'content': '\n'.join(
            f'{notification_map[op]} {ev}'
            for op, ev in notifications
        )}
    )

# EOF
