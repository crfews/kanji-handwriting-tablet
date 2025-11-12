import datetime

class FieldType:
    _id: int
    _name: str
    _is_text: bool
    _is_int: bool
    _is_pickle: bool
    _owning_card_type: 'CardType'

    def __init__(self):
        pass

    def get_id(self) -> int:
        return self._id

    def get_name(self) -> str:
        return self._name

    def get_instances(self) -> list['Field']:
        pass

class Field:
    _id: int
    _name: str
    _is_text: bool
    _is_int: bool
    _is_pickle: bool
    _owning_card: 'Card'

    def __init__(self):
        pass

    def get_id(self) -> int:
        return self._id

    def get_name(self) -> str:
        return self._name

    def get_instances(self) -> list['Field']:
        pass

    def get_owning_card(self) -> 'Card':
        pass

   
class CardType:
    _id: int
    _name: str
    _owned_cards: list['Card']
    _owned_field_types: list[FieldType]

    def __init__(self):
        pass
    
    def get_id(self) -> int:
        return self._id

    def get_name(self) -> str:
        return self._name

    def get_instances(self) -> list['Card']:
        pass
    

class Card:
    _id: int
    _study_id: int
    _owning_card_type: CardType
    _owned_fields: list[Field]
    _studied: bool
    _due_date_increment: int
    _due_date: datetime.date

    def __init__(self):
            pass

    def get_id(self) -> int:
        return self._id

    def get_study_id(self) -> int:
        pass

    def get_owning_card_type(self) -> CardType:
        pass
    
    def get_fields(self) -> list['Fields']:
        pass

    
# class Card:

#     # initializes card object with all necessary attributes
#     def __init__(self,config):
#         self.id = config['id']
#         self.study_id = config['study_id']
#         self.answer = config['answer']
#         self.increment = config['increment']
#         self.related_cards = config['related_cards']
#         self.information = config['information']
#         self.type = config['type']
#         self.max_related_id = config['max_related_id']

#     # adds to databsse
#     def insert(self):
#         pass
 
