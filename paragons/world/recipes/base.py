from random import randint 
from evennia.utils import iter_to_str
from evennia.contrib.game_systems.crafting import CraftingRecipe


class SkillRecipe(CraftingRecipe):
    skill = (None, 0)
    exp_gain = 0

    def craft(self, **kwargs):
        # set at initialization
        crafter = self.crafter 

        # assume the skill is stored directly on the crafter 
        req_skill, difficulty = self.skill 

        if not req_skill or not difficulty:
            return super().craft(**kwargs)
        
        crafting_skill = crafter.traits.get(req_skill)

        if not crafting_skill:
            self.msg("You do not know how to make this.")
            return 
        
        elif crafting_skill.value < difficulty:
            self.msg("You are not good enough to make this yet. Better keep practicing!")
            return 
        
        success_rate = crafting_skill.value - difficulty 

        crafter.traits.fp.current -= 5

        if self.exp_gain:
            exp = crafter.attributes.get("exp", 0)
            crafter.db.exp = self.exp_gain + exp 

        if not randint(0, success_rate):
            self.msg("It doesn't work out, maybe you should try again?")
            return 
        
        return super().craft(**kwargs)