from collections import Counter
from evennia import CmdSet 
from evennia.utils import make_iter 
from evennia.utils.evtable import EvTable
from .commands import Command



class CmdList(Command):
    """\
    View a list of items available for sale.
    """ 
    key = "list"
    aliases = ("browse", )
    help_category = "here"

    def func(self):
        if not (storage := self.obj.db.storage):
            self.msg("This shop is not open for business.")
            return
        listings = []
        for obj in storage.contents:
            if price := obj.db.price:
                listings.append((obj.name, price))

        condensed = Counter(listings)
        listings = [[key[0], val, key[1]] for key, val ]


class ShopCmdSet(CmdSet):
    pass


class CmdMoney(Command):
    def func(self):
        pass

    