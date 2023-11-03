MAP_STR = """?"""

weight = 1
_MAX_NODES = 50
_MAX_MOBS = 50


MAP_KEY = {
    "%": {
        "biome": "forest",
        "desc": "There are many trees here.",
        "gathers": (
            ("APPLE_TREE", 1),
            ("LUMBER_TREE", 5),
        ),
        "node cap": 10,
        "mobs": (("DOE_DEER", 3), ("STAG_DEER", 1), ("SQUIRREL", 5)),
        "mob cap": 25,
    },
    '"': {
        "biome": "grass",
        "desc": "A grassy meadow.",
        "gathers": (
            ("APPLE_TREE", 1),
            ("LUMBER_TREE", 5),
        ),
        "node cap": 10,
        "mobs": (("DOE_DEER", 3), ("STAG_DEER", 1), ("PHEASANT", 10)),
        "mob cap": 15,
    },
    ".": {
        "biome": "beach",
        "desc": "The sand and rocks slope gently into the ocean waves.",
        "gathers": (("DRIFTWOOD", 1),),
    },
    "^": {
        "biome": "mountains",
        "desc": "The ground slopes sharply, littered with rocks and boulders.",
        "gathers": (("IRON_ORE_NODE", 1), ("COPPER_ORE_NODE", 5)),
        "node cap": 25,
        "mobs": (("ANGRY_BEAR", 1), ("COUGAR", 5)),
        "mob cap": 15,
    },
    "O": {
        "biome": "city",
        "desc": "You stand outside of a city.",
    },
}

from random import randint, choices
from evennia.contrib.grid.wilderness import wilderness 
from evennia.prototypes import spawner 
from evennia.utils.search import search_tag 
from evennia.utils import logger, pad


class OverworldMapProvider(wilderness.WildernessMapProvider):
    room_typeclass = "typeclasses.rooms.OverworldRoom"
    exit_typeclass = "typeclasses.exits.OverworldExit"

    def is_valid_coordinates(self, wilderness, coordinates):
        x, y = coordinates 

        rows = MAP_STR.split('\n')
        rows.reverse()

        if y not in range(len(rows)):
            return False 
        
        row = rows[y]

        if x not in range(len(row)):
            return False 
        
        tile = row[x]

        return tile in MAP_KEY
    
    def get_location_name(self, coordinates):
        x, y = coordinates 

        rows = MAP_STR.split("\n")
        rows.reverse()

        tile = rows[y][x]
        tile_data = MAP_KEY.get(tile, {})
        return f"In the {tile_data.get('biome', 'wilderness')}"
    
    def at_prepare_room(self, coordinates, caller, room):
        x, y = coordinates 


        rows = MAP_STR.split("\n")
        rows.reverse()
        tile = rows[y][x]
        tile_data = MAP_KEY.get(tile, {})

        room.ndb.active_desc = tile_data.get("desc")

        border = "-" * 29
        minimap = [border]
        for i in range(y + 2, y - 3, -1):
            row = rows[i][x - 2 : x + 3]
            if i == y:
                row = row[:2] + "|g@|n" + row[3:]
            minimap.append(" " * 12 + row + " " * 12)
        minimap.append(border)
        room.ndb.minimap = "\n".join(minimap)

        if not randint(0, 5):
            self.spawn_resource(
                room,
                coordinates,
                tile_data.get("gathers"),
                cap=tile_data.get("node cap", _MAX_NODES),
                tag=tile_data.get("biome"),
                tag_cat="resource_node"
            )
        elif not randint(0, 10):
            mob = self.spawn_resource(
                room, 
                coordinates,
                tile_data.get("mobs"),
                cap=tile_data.get("mob cap", _MAX_MOBS), 
                tag=tile_data.get("biome"),
                tag_cat="mob"
            )
            if mob:
                mob.at_character_arrive(caller)

    def spawn_resource(self, room, coordinates, weighted_options, **kwargs):
        if not weighted_options:
            return 
        
        if (tag := kwargs.get("tag")) and (tag_cat := kwargs.get("tag_cat")):
            if spawn_cap := kwargs.get("cap"):
                tagged = search_tag(key=tag, category=tag_cat)
                if len(tagged) >= spawn_cap:
                    return
                
        options, weights = zip(*weighted_options)
        protkey = choices(options, weights=weights)[0]

        try:
            obj = spawner.spawn(protkey)[0]
        except KeyError as e:
            logger.log_msg(f"   {e} on {protkey}")
            return
        
        room.wilderness.move_obj(obj, coordinates)
        if tag and tag_cat:
            obj.tags.add(tag, category=tag_cat)

        return obj
    

def create():
    wilderness.create_wilderness(
        mapprovider=OverworldMapProvider(),
        name="overworld",
        preserve_items=True
    )

def enter(obj, coordinates):
    wilderness.enter_wilderness(obj, coordinates=coordinates, name="overworld")