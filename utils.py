import math
import celcat

COLORS = [
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

    for hex_color in COLORS:
        rgb = hex_to_rgb(hex_color)
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(target_rgb, rgb)))
        if distance < min_distance:
            min_distance = distance
            closest_color = hex_color
    
    return str(COLORS.index(closest_color) + 1)

# EOF