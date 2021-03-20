from parser_zak import Parser
from data.db_session import create_session, global_init
from data.models import History, User, Data
from datetime import datetime
import multiprocessing as mp
import time


class ParserController:
    def __init__(self, parser_limit=3) -> None:
        self.parsers = []
        self.queue = []
        self.parser_limit = parser_limit
        self.mp_queue = mp.Queue()
    
    def add_parser(self, user_id, parameters:dict):
        parser = Parser(parameters)
        history = self._create_history(user_id, parameters)
        self.mp_queue.put_nowait([parser, history])

    
    def start_loop(self):
        self.loop_process = mp.Process(target=self.loop, args=(self.mp_queue, ))
        self.loop_process.start()


    def loop(self, queue:mp.Queue):
        global_init('db/db.sqlite')
        self.session = create_session()
        while True:
            if queue.qsize():
                element = queue.get()
                self.process_handler(element)
                queue.put(self.parsers)
            
            if len(self.parsers) > 0:
                for i in range(len(self.parsers)):
                    if i >= len(self.parsers):
                        break
                    
                    data = self.parsers[i][0].pipe[0].recv()
                    if data.__class__ == str:
                        if data == 'end':
                            print('end')
                            self.parsers[i][1].state = 'завершён'
                            self.session.commit()
                            del self.parsers[i]
                            self.move_queue()
                        else:
                            print(data)
                    elif data.__class__ == Data:
                        self.parsers[i][1].document += self.data_handler(data) + '\n'
                        print(data.id)
                    else:
                        print(data)
                        

            else:
                time.sleep(3)


    def data_handler(self, data: Data):
        row = ''
        row += ';'.join([str(data.id), data.type, str(data.tender_price), data.tender_date.strftime('%d.%m.%Y'),
                         data.tender_object, data.customer, data.tender_adress, data.tender_delivery, data.tender_terms])
        row += f'"{data.document_links}";'
        row += data.tender_link + ';'

        winner = data.winner[0]
        row += ';'.join([winner.name, winner.position, winner.price])
        return row
    
    def process_handler(self, element:list):
        if len(self.parsers) >= self.parser_limit:
            element[1].state = 'в очереди'
            print('в очереди')
            self.session.add(element[1])
            self.session.commit()
            self.queue.append(element)
        else:
            element[1].state = 'в процессе'
            print('работает')
            element[0].start_async()
            self.session.add(element[1])
            self.session.commit()
            self.parsers.append(element)
    
    def move_queue(self):
        if len(self.queue) > 0:
            element = self.queue.pop(0)
            element[1].state = 'в процессе'
            self.session.commit()
            self.parsers.append(element)
    

    def _create_history(self, user_id:int, parameters: dict):
        history = History()
        history.user_id = user_id
        history.tag = parameters.get('searchString')
        history.state = ''
        history.document = ''
        if 'priceFromGeneral' in parameters:
            history.min_price = int(parameters['priceFromGeneral'])
        if 'priceToGeneral' in parameters:
            history.max_price = int(parameters['priceToGeneral'])
        if 'publishDateFrom' in parameters:
            history.date_from = datetime.strptime(
                parameters['publishDateFrom'], '%d.%m.%Y')
        if 'publishDateTo' in parameters:
            history.date_to = datetime.strptime(
                parameters['publishDateTo'], '%d.%m.%Y')
        history.sort_filter = parameters['search-filter']
        if parameters['sortDirection'] == 'false':
            history.sort_direction = False
        else:
            history.sort_direction = True
        return history
