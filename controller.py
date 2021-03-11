from parser_zak import Parser
from data.models import Data
from data.db_session import create_session



class ParserController:
    def __init__(self, database, parser_limit=3) -> None:
        self.db = database
        self.parsers = []
        self.queue = []
        self.parser_limit = 3
        self.db_session = create_session()
    
    def add_parser_from_request(self, request):
        data = user.