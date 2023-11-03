from .base import SkillRecipe 


class BoneHiltRecipe(SkillRecipe):
    """
    Carve a hilt out of bone.
    """

    skill = ("whittling", 5)
    exp_gain = 5

    name = "bone hilt"
    tool_tags = ["knife"]
    consumable_tags = ["bone", "leather"]
    output_prototypes = [
        {
            "key": "bone hilt",
            "desc": "A leather-wrapped hilt for a bladed weapon, carved out of bone.",
            "tags": [("hilt", "crafting_material")],
            "value": 5
        }
    ]


class WoodHiltRecipe(SkillRecipe):
    """
    Carve a hilt out of wood.
    """

    skill = ("whittling", 5)
    exp_gain = 3

    name = "wooden hilt"
    tool_tags = ["knife"]
    consumable_tags = ["wood", "leather"]
    output_prototypes = [
        {
            "key": "wooden hilt",
            "desc": "A leather-wrapped hilt for a bladed weapon, carved out of wood.",
            "tags": [("hilt", "crafting_material")],
            "value": 5
        }
    ]