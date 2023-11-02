"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia.objects.objects import DefaultRoom
from evennia.utils import create, iter_to_str, logger 
from evennia.contrib.grid.xyzgrid.xyzroom import XYZRoom
from evennia.contrib.grid.wilderness.wilderness import WildernessRoom

from .objects import ObjectParent
from .scripts import RestockScript 

from commands.shops import ShopCmdSet
from commands.skills import TrainCmdSet


class RoomParent(ObjectParent):
    def at_object_receive(self, mover, source_loc, move_type=None, **kwargs):
        super().at_object_receive(mover, source_loc, **kwargs)
        if 'character' in mover._content_types:
            for obj in self.contents_get(content_type='character'):
                if obj == mover:
                    continue 
                obj.at_character_arrive(mover, **kwargs)

    def at_object_leave(self, mover, destination, **kwargs):
        super().at_object_leave(mover, destination, **kwargs)
        if combat := self.scripts.get("combat"):
            combat = combat[0]
            combat.remove_combatant(mover)
        if 'character' in mover._content_types:
            for obj in self.contents_get(content_type='character'):
                if obj == mover:
                    continue 
                obj.at_character_depart(mover, destination, **kwrargs)

    def get_display_footer(self, looker, **kwargs):
        cmd_keys = [
            f"|w{cmd.key}|n"
            for cmdet in self.cmdset.all()
            for cmd in cmdset
            if cmd.access(looker, 'cmd')
        ]
        if cmd_keys:
            return f"Area commands available: {', '.join(cmd_keys)}"
        else:
            return ""



class Room(RoomParent, DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """

    pass


class OverworldRoom(RoomParent, WildernessRoom):
    def get_display_header(self, looker, **kwargs):
        if not self.ndb.minimap:
            self.ndb.minimap = self.db.minimap
        return self.ndb.minimap or ""

    def at_server_reload(self, **kwargs):
        self.db.desc = self.ndb.active_desc 
        self.db.minimap = self.ndb.minimap 



class XYGridRoom(RoomParent, XYZRoom):
    pass


class XYGridShop(XYGridRoom):
    def at_object_creation(self):
        super().at_object_creation()
        self.cmdset.add(ShopCmdSet, persistent=True)

        self.db.storage = create.object(
            key='shop storage',
            locks="view:perm(Builder);get:perm(Builder)",
            home=self,
            location=self
        )
        self.scripts.add(RestockScript, key='restock', autostart=False)

    def add_stock(self, obj):
        if storage := self.db.storage:
            obj.location = storage 
            val = obj.db.value or 0
            obj.db.price = val * 2
            return True 
        else:
            return False 



class XYGridTrain(XYGridRoom):
    def at_object_creation(self):
        super().at_object_creation()
        self.cmdset.add(TrainCmdSet, persistent=True)



class XYZShopNTrain(XYGridTrain, XYGridShop):
    pass