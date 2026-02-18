'''Module containing the scheduling logic and functions for reviewing cards'''



################################################################################
# Imports
################################################################################



from data import *
from datetime import datetime, date, timedelta
import sqlalchemy as sqla



################################################################################
# Globals Definition
################################################################################



GOOD = 1    # Increase 0->1 day, 1->3days, etc
OK = -1     # Decrease 3->1day, 1->0days, etc
BAD = 0     # Restart, Due/study today
DAYS_INCREMENT: list[int] = [0, 1, 3, 7, 14, 30, 90, 180, 365]
INCREMENT_COUNT = len(DAYS_INCREMENT)



################################################################################
# Private Function Definitions
################################################################################



def _add_dates(inc: int) -> date:
    '''Returns a date 'inc' days into the future from today'''
    
    assert inc < INCREMENT_COUNT
    return (datetime.today() + timedelta(days=DAYS_INCREMENT[inc])).date()



def _update_card(c: Card, new_inc: int, con: None | sqla.Connection) -> date:
    '''Checks if 'new_inc' is a valid index in 'DAYS_INCREMENT' and updates the
    due_date_increment of the card if so. Otherwise it keeps the old due_date_increment.
    It then sets the due_date of the card to increment + today. Returns the new due_date
    of the card.'''
    
    # If the new increment is a valid index then update, otherwise keep the old increment
    if new_inc >= 0 and new_inc < INCREMENT_COUNT:
        c.due_date_increment = new_inc
        
    c.due_date = _add_dates(c.due_date_increment)
    c.sync(con=con) # Pass the connection in the event the user is batch modifying
    return c.due_date
    


################################################################################
# Public Function Definitions
################################################################################



def review_card_good(c: Card, con: None | sqla.Connection = None) -> date:
    return _update_card(c, c.due_date_increment + GOOD, con)
    


def review_card_ok(c: Card, con: None | sqla.Connection):
    return _update_card(c, c.due_date_increment + OK, con)



def review_card_bad(c: Card, con: None | sqla.Connection) -> date:
    return _update_card(c, BAD, con)
