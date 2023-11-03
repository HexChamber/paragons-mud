from evennia.contrib.grid.xyzgrid import xymap_legend 


MAP_STR = r"""
+
                               
5   o-----G-----G---R---R---o  
    |      \    |           |  
4   R     B-R $-R   $-B B   R  
    |        \  |   |/  |   |  
3   G-----R---#-#---R---R---G  
    |          \    |   |   |  
2   R         $-R-$ B   B   R  
    |            \          |  
1   o---R-----R---G-----R---o  
                               
0                              

+
"""



class RoadNode(xymap_legend.MapNode):
    display_symbol = "#"
    prototype = {
        "prototype_parent": "xyz_room",
        "tags": [("Kyle", "zone")],
        "key": "A road",
        "desc": "A wide road through Kyle."
    }


class GateNode(xymap_legend.MapNode):
    display_symbol = "Ø"
    prototype = {
        "prototype_parent": "xyz_room",
        "tags": [("Kyle", "zone")],
        "key": "A road",
        "desc": "The road here leads out of Kyle and into the wilderness."
    }


class ShopNode(xymap_legend.MapNode):
    prototype = {
        "prototype_parent": "xyz_room",
        "typeclass": "typeclasses.rooms.XYGridShop",
        "key": "Inside",
        "desc": "A shop in Kyle."
    }


class BuildingNode(xymap_legend.MapNode):
    prototype = {
        "prototype_parent": "xyz_room",
        "key": "Inside",
        "desc": "A building in Kyle."

    }

LEGEND = {
    "R": RoadNode,
    "G": GateNode,
    "B": BuildingNode,
    "$": ShopNode
}


PROTOTYPES = {}

XYMAP_DATA = {
    "zcoord": "kyle",
    "map": MAP_STR,
    "legend": LEGEND,
    "prototypes": PROTOTYPES,
    "options": {"map_visual_range": 1},
}