import httpx
import urllib.parse
from typing import Iterator
from datetime import datetime
from dataclasses import dataclass, field

DATEFMT = '%Y-%m-%d'
TIMEFMT = DATEFMT + 'T%H:%M:%S'


@dataclass(frozen = True)
class Result:
    id: str
    text: str
    dept: str

@dataclass(frozen = True)
class Event:
    id: str
    start: datetime
    end: datetime
    text: str
    sites: list[str]
    modules: list[str]
    type: str
    data: dict[str] = field(repr = False)
    
    @classmethod
    def parse(cls, **data) -> object:
        
        return cls(
            id = data['id'],
            start = datetime.strptime(data['start'], TIMEFMT),
            end = datetime.strptime(data['end'], TIMEFMT),
            text = data['description'],
            sites = data['sites'],
            modules = data['modules'],
            type = data['eventCategory'],
            data = data
        )


class Client(httpx.Client):
    '''
    Represents a Celcat client.
    '''
    
    def __init__(self, server: str, ressource: int = 103) -> None:
        ''''''
        
        self.root = urllib.parse.urljoin(server, 'Home/')
        self.ressource = ressource
        super().__init__()
    
    def _yield(self, response: httpx.Response, factory: object, hint: str = None) -> Iterator[object]:
        '''
        Validates and iterate a response.
        '''
        
        response.raise_for_status()
        assert response.content, 'No data found'
        data = response.json()
        if hint: data = data[hint]
        
        for item in data:
            yield factory(**item)
    
    def search(self, query: str, max: int = 50) -> Iterator[Result]:
        '''
        Search for groups.
        '''
        
        return self._yield(
            response = self.get(
                url = self.root + 'ReadResourceListItems',
                params = {
                    'myRessources': False,
                    'searchTerm': query,
                    'pageSize': max,
                    'pageNumber': 1,
                    'resType': self.ressource
                }
            ),
            factory = Result,
            hint = 'results'
        )
    
    def fetch(self, groups: list[str], start: datetime, end: datetime) -> Iterator[Event]:
        '''
        Get calendar data.
        '''
        
        return self._yield(
            response = self.post(
                url = self.root + 'GetCalendarData',
                data = {
                    'start': start.strftime(DATEFMT),
                    'end': end.strftime(DATEFMT),
                    'resType': self.ressource,
                    'calView': 'agendaDay',
                    'federationIds[]': groups,
                    'colourScheme': 3
                }
            ),
            factory = Event.parse
        )

# EOF