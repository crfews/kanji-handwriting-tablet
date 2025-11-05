

class Card:

    # initializes card object with all necessary attributes
    def __init__(self,config):
        self.id = config['id']
        self.study_id = config['study_id']
        self.answer = config['answer']
        self.increment = config['increment']
        self.related_cards = config['related_cards']
        self.information = config['information']
        self.type = config['type']
        self.max_related_id = config['max_related_id']

    # adds to databsse
    def insert(self):
        pass
    
    




