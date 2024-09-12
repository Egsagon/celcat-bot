import time
import yaml
import math
import httpx
import celcat
import logging
import traceback
from gcsa.event import Event
from datetime import datetime, timedelta
from gcsa.google_calendar import GoogleCalendar

logger = logging.getLogger('app')

logging.basicConfig(
    level = 'INFO',
    format = '%(asctime)-14s %(levelname)-8s ~ %(name)s: %(message)s',
    datefmt = '%H:%M:%S %d/%m'
)

logger.info('Reading config')
with open('config.yml') as file:
    config = yaml.safe_load(file)

logger.info('Connecting to Google')
calendar = GoogleCalendar(
    credentials_path = 'creds.json'
)

logger.info('Connecting to Celcat server')
client = celcat.Client(
    server = config['celcat']['server'],
    ressource = config['celcat']['ressource']
)

google_colors = [
    '#7986CB', '#33B679', '#8E24AA', '#E67C73',
    '#F6BF26', '#F4511E', '#039BE5', '#616161',
    '#3F51B5', '#0B8043', '#D50000'
]


def hex_to_rgb(hex_color):
    '''
    Converts an HEX color to RGB.
    '''
    
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_color(item: celcat.Event):
    '''
    Get a Google color ID based on the Celcat HEX color.
    '''
    
    target_hex = item.data.get('backgroundColor', '#8E24AA')
    target_rgb = hex_to_rgb(target_hex)
    closest_color = None
    min_distance = float('inf')

    for hex_color in google_colors:
        rgb = hex_to_rgb(hex_color)
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(target_rgb, rgb)))
        if distance < min_distance:
            min_distance = distance
            closest_color = hex_color
    
    return str(google_colors.index(closest_color) + 1)

def update() -> None:
    '''
    Harvest data and updates the calendar.
    '''
    
    logger.info('Starting update')
    
    data = client.fetch(
        groups = config['celcat']['groups'],
        start = datetime.now(),
        end = datetime.now() + timedelta(**config['app']['distance'])
    )
    
    # Remove all future celcat events
    for event in calendar.get_events(
        time_min = datetime.now().replace(hour = 0, minute = 0),
        timezone = config['celcat']['timezone'],
        query = '[CELCAT EVENT]'
    ):
        logger.info(f'Deleting event "{event}"')
        calendar.delete_event(event)
    
    # Rewrite each event
    for event in data:
        logger.info(f'Writing event "{event.id}"')
        
        calendar.add_event(Event(
            start = event.start,
            end = event.end,
            timezone = config['celcat']['timezone'],
            location = 'Celcat',
            summary = f'{event.type} - {"+".join(event.modules or "?")}',
            description = event.text + '\n\n[CELCAT EVENT]',
            color_id = get_color(event)
        ))


if __name__ == '__main__':
    
    interval = timedelta(**config['app']['interval'])
    
    while 1:
        try:
            update()
        
        except Exception as err:
            logger.exception(err)
            
            # Send to webhook
            tb = '\n'.join(traceback.format_tb(err.__traceback__, 3))
            httpx.post(
                url = config['app']['webhook'],
                json = {
                    'embeds': [{
                        'title': f'Error ({err.__class__.__name__})',
                        'color': 16711680,
                        'description': ' '.join(err.args),
                        'fields': [{
                            'name': '',
                            'value': f'```py\n{tb}```'
                        }]
                    }]
                }
            ).raise_for_status()
        
        # Wait for next update
        next = (datetime.now() + interval).strftime('%H:%M')
        logger.info(f'Scheduling next update at {next}')
        time.sleep(interval.total_seconds())

# EOF