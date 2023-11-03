from collections import Counter
from evennia import CmdSet 
from evennia.utils import make_iter 
from evennia.utils.evtable import EvTable
from .command import Command



class CmdList(Command):
    """
    View a list of available items for sale.
    """

    key = "list"
    aliases = ("browse",)
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
        listings = [[key[0], val, key[1]] for key, val in condensed.items()]
        if not condensed:
            self.msg("This shop has nothing for sale right now.")
            return 
        
        table = EvTable("Item", "Amt", "Price", border="rows")
        for key, val in condensed.items():
            table.add_row(key[0], val, key[1])

        self.msg(str(table))



class CmdBuy(Command):
    """
    Attempt to buy an item from this shop.

    Usage:
        - `buy <obj>`
        - `buy <num> <obj>`
    
    Example:
        - `buy iron sword`
        - `buy 12 arrow`
    """
    key = 'buy'
    aliases = ('order', "purchase")
    help_category="here"

    def parse(self):
        self.args = self.args.strip()
        first, *rest = self.args.split(" ", maxsplit=1)

        if not rest:
            self.count = 1
        elif first.isdecimal():
            self.count = int(first)

            self.args = " ".join(rest)

        else:
            self.count = 1
        
    def func(self):
        if not (storage := self.obj.db.storage):
            self.msg("This shop is not open for business.s")
            return 
        
        if not (coins := self.caller.db.coins):
            self.msg("You don't have any money!")
            return 
    
        objs = self.caller.search(self.args, location=storage, stacked=self.count)
        if not objs:
            return 
        
        objs = make_iter(objs)
        objs = [obj for obj in objs if obj.price]
        if not objs:
            self.msg(f"There are no {self.args} for sale.")
            return
        
        example = objs[0]
        count = len(objs)
        obj_name = example.get_numbered_name(count, self.caller)[1]

        total = sum([obj.attributes.get("price", 0) for obj in objs])

        if coins < total:
            self.msg(f"You need {total} coins to buy that.")
            return 
        
        confirm = yield(f"Confirming you want to buy {obj_name} for {total}? [yes/No]")

        if confirm.lower().strip() not in ("yes", "y"):
            self.msg("Purchase cancelled.")
            return 
        
        for obj in objs:
            obj.location = self.caller

        self.caller.db.coins -= total

        self.msg(f"You exchange {total} coins for {count} {obj_name}.")



class CmdSell(Command):
    """
    Offer something for sale to a shop.

    Usage:
        - `sell <obj>`
        - `sell <num> <obj>`

    Example:
        - `sell sword`
        - `sell 5 apple`
    """
    key = 'sell'
    help_category = 'here'

    def parse(self):
        self.args = self.args.strip()

        first, *rest = self.args.split(' ', maxsplit=1)

        if not rest:
            self.count = 1
        
        elif first.isdecimal():
            self.count = int(first)
            self.args = " ".join(rest)
        else:
            self.count = 1

    def func(self):
        if not (storage := self.obj.db.storage):
            self.msg("This shop is not open for business.")
            return 
        
        objs = self.caller.search(self.args, location=self.caller, stacked=self.count)
        if not objs:
            return 
        
        objs = make_iter(objs)
        example = objs[0]
        count = len(objs)
        obj_name = example.get_numbered_name(count , self.caller)[1]

        total = sum([obj.attributes.get('price', 0) for obj in objs])

        confirm = yield(f"Confirming that you want to sell {obj_name} for {total}? [yes/No]")

        if confirm.lower().strip() not in ("yes", "y"):
            self.msg("Sale cancelled.")
            return 
        
        for obj in objs:
            self.obj.add_stock(obj)

        coins = self.caller.db.coins or 0
        self.caller.db.coins = coins + total

        self.msg(
            f"You exchange {obj_name} for {total} coin{'' if total == 1 else 's'}."
        )


class ShopCmdSet(CmdSet):
    key = "Shop CmdSet"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()

        self.add(CmdList)
        self.add(CmdBuy)
        self.add(CmdSell)


class CmdMoney(Command):
    """
    View your total wealth measured in coins.

    Usage: 
        - `coins`
    """
    key = 'coins'
    aliases = ('wallet', 'money', 'gp')

    def func(self):
        coins = self.caller.db.coins or "no"
        self.msg(f"You have {coins} coin{'' if coins == 1 else 's'}.")
