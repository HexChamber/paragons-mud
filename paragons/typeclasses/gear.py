from random import choice
from evennia import AttributeProperty
from evennia.utils import logger 
from evennia.contrib.game_systems.containers import ContribContainer 

from .objects import Object, ClothingObject 


class BareHand:
    damage = 1
    energy_cost = 3
    skill = 'unarmed'
    name = 'fist'
    speed = 5

    def at_pre_attack(self, wielder, **kwargs):
        if wielder.traits.ep.value < self.energy_cost:
            wielder.msg("You are too exhausted to hit anything.")
            return False 
        if not wielder.cooldowns.ready('attack'):
            wielder.msg("You can't attack again yet.")
            return False 
    
        return True

    def at_attack(self, wielder, target, **kwargs):
        damage = self.damage
        wielder.traits.ep.current -= self.energy_cost 
        if not damage:
            wielder.at_emote(
                f"$conj(swings) $pron(your) {self.name} at $you(target), but $conj(misses).",
                mapping={'target': target}
            )
        else:
            wielder.at_emote(
                f"$conj(hits) $you(target) with $pron(your) {self.name}.",
                mapping={'target': target}
            )
            target.at_damage(wielder, damage, 'bludgeon')
        wielder.msg(f"[ Cooldown: {self.speed} seconds ]")
        wielder.cooldowns.add('attack', self.speed)

    
class MeleeWeapon(Object):
    speed = AttributeProperty(10)

    def at_pre_attack(self, wielder, **kwargs):
        if wielder.traits.ep.value < self.attributes.get("energy_cost", 0):
            wielder.msg("You are too exhausted to use this.")
            return False 
        if not wielder.cooldowns.ready('attack'):
            wielder.msg("You can't attack aggain yet.")
            return False 
        if self not in wielder.wielding:
            wielder.msg(
                f"You must be wielding your {self.get_display_name(wielder)} to attack with it."
            )
            return False 
        else:
            return True 

    def at_attack(self, wielder, target, **kwargs):
        damage = self.db.dmg
        damage_type = None 
        if damage_types := self.tags.get(category="damage_type", return_list=True):
            damage_type = choice(damage_types)

        if skill := self.tags.get(category="skill_class"):
            result = wielder.use_skill(skill, speed=self.speed)

            damage = damage * result 

        wielder.traits.ep.current -= self.attributes.get('energy_cost', 0)
        if not damage:
            wielder.at_emote(
                "$conj(swings) {weapon} at $you(target), but $conj(misses).",
                mapping={
                    "target": target,
                    "weapon": self
                }
            )
        else:
            wielder.at_emote(
                f"$conj({damage_type or 'swings'}) $you(target) with $pron(their) {{weapon}}.",
                mapping={
                    'target': target,
                    'weapon': self
                }
            )
            target.at_damage(wielder, damage, damage_type)
        wielder.msg(f"[ Cooldown: {self.speed} seconds ]")
        wielder.cooldowns.add('attack', self.speed)
        

class WearableContainer(ContribContainer, ClothingObject):
    pass

