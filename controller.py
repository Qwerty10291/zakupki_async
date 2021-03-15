from flask.globals import session
from parser_zak import Parser
from data.models import Data
from data.db_session import create_session
from data.models import History, User
from datetime import datetime
from io import BytesIO
import csv

class ParserController:
    def __init__(self, parser_limit=3) -> None:
        self.parsers = []
        self.queue = []
        self.parser_limit = parser_limit
        self.state = False
    
    def add_parser(self, user_id, parameters:dict):
        session = create_session()
        parser = Parser(parameters)
        if len(self.parsers) > self.parser_limit:
            history = self._create_history('в очереди', user_id, parameters)
            self.queue.append([parser, history])
            session.add(history)
            session.commit()
        else:
            history = self._create_history('в процессе', user_id, parameters)
            session.add(history)
            session.commit()
            self.parsers.append([parser, history,])
            parser.start_async()
        if not self.state:
            self.loop()
    
    def loop(self):
        session = create_session()
        self.state = True
        while True:
            for i in range(len(self.parsers)):
                if i >= len(self.parsers):
                    break
                
                data = self.parsers[i][0].pipe[0].recv()
                if data is dict:
                    print(data['tender_object'])
                elif data is str:
                    if data == 'end':
                        self.parsers[i][1].state = 'завершён'
                    session.commit()
                    del self.parsers[i]
                else:
                    print(data)
            if len(self.parsers) == 0:
                self.state = False
                break


    def update_queue(self):
        session = create_session()
        if len(self.queue) > 0:
            parser = self.queue.pop(0)
            parser[1].state = 'в процессе'
            parser[0].start_async()
            self.parsers.append(parser)
            session.commit()
        else:
            return True
        
    
    def _create_history(self, state, user_id, parameters:dict):
        history = History()
        history.user_id = user_id
        history.state = state
        history.tag = parameters.get('searchString')
        if 'priceFromGeneral' in parameters:
            history.min_price = int(parameters['priceFromGeneral'])
        if 'priceToGeneral' in parameters:
            history.max_price = int(parameters['priceToGeneral'])
        if 'publishDateFrom' in parameters:
            history.date_from = datetime.strptime(parameters['publishDateFrom'], '%d.%m.%Y')
        if 'publishDateTo' in parameters:
            history.date_to = datetime.strptime(parameters['publishDateTo'], '%d.%m.%Y')
        history.sort_filter = parameters['search-filter']
        if parameters['sortDirection'] == 'false':
            history.sort_direction = False
        else:
            history.sort_direction = True
        return history