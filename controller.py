from parser_zak import Parser


class ParserController:
    def __init__(self, database, parser_limit=3) -> None:
        self.db = database
        self.parsers = []

        self.queue = []

        self.parser_limit = 3
    
    def add_parser_from_request(self, request):
        if len(self.parser) == self.parser_limit:
            self.queue.append()