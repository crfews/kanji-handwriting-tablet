# Author: Phillip Graham
# Description: Defines a class used to wrap the table of relationships between
# cards
# Last Modified: Wed. Feb. 02, 2026
 

################################################################################
# Imports
################################################################################

from __future__ import annotations
from typing import Mapping
import sqlalchemy as sqla
from .database import _engine, card_relation_table, maybe_connection, maybe_connection_commit
from .card import Card
from typing import TYPE_CHECKING

# satisfy pyright
if TYPE_CHECKING:
    from .card import Card
    
################################################################################
# Class Definition
################################################################################

