"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from random import randint 
from string import punctuation 
from evennia import AttributeProperty 
from evennia.utils import lazy_property, iter_to_str, delay, logger
from evennia.prototypes.spawner import spawn
from evennia.contrib.rpg.traits import TraitHandler 
from evennia.contrib.game_systems.clothing.clothing import ClothedCharacter, get_worn_clothes
from evennia.contrib.game_systems.cooldowns import CooldownHandler
from evennia.objects.objects import DefaultCharacter

from .objects import ObjectParent

_IMMOBILE = (
    "sitting",
    "lying down",
    "unconscious",
)


class Character(ObjectParent, ClothedCharacter):
    """
    The Character defaults to reimplementing some of base Object's hook methods with the
    following functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead).
    at_post_move(source_location) - Launches the "look" command after every move.
    at_post_unpuppet(account) -  when Account disconnects from the Character, we
                    store the current location in the pre_logout_location Attribute and
                    move it to a None-location so the "unpuppeted" character
                    object does not need to stay on grid. Echoes "Account has disconnected"
                    to the room.
    at_pre_puppet - Just before Account re-connects, retrieves the character's
                    pre_logout_location Attribute and move it back on the grid.
    at_post_puppet - Echoes "AccountName has entered the game" to the room.

    """

    gender = AttributeProperty('plural')

    @property 
    def in_combat(self):
        if not (location := self.location):
            return False 
        if not (combat := location.scripts.get("combat")):
            return False 
        
        return self in combat[0].fighters 

    @property 
    def can_flee(self):
        if not (evade := self.use_skill("evasion")):
            evade = self.db.agi 
        
        if (randint(0, 99) - self.traits.fp.value) < evade:
            return True 
        else:
            self.msg("You can't find an oppurtunity to escape.")
            return False 
        
    @lazy_property
    def traits(self):
        return TraitHandler(self)

    @lazy_property
    def cooldowns(self):
        return CooldownHandler(self, db_attribute="cooldowns")

    @property
    def wielding(self):
        return [obj for obj in self.attributes.get('_wielded',{}).values() if obj]

    @property
    def free_hands(self):
        return [
            key for key, val in self.attributes.get('_wielded', {}).items() if not val
        ]
    
    def defense(self, damage_type=None):
        # if damage_type is not None:
        #     resistance = self.attritutes.get('resistances')
        #     resistance = resistance.get("")
        defense = sum([obj.attributes.get("armor", 0) for obj in get_worn_clothes(self) + [self]])
        if damage_type is not None:
            resistance_table = self.attributes.get('resistances')
            resistance = resistance_table.get(damage_type)
            if resistance is not None:
                defense += resistance
        return defense

    def at_object_creation(self):
        self.db.str = 5
        self.db.agi = 5
        self.db.wil = 5
        self.traits.add(
            "hp",
            "Health",
            trait_type="gauge",
            min=0,
            max=100,
            base=100,
            rate=0.1
        )
        self.traits.add(
            'fp',
            "Focus",
            trait_type="gauge",
            min=0,
            max=100,
            base=100,
            rate=0.1
        )
        self.traits.add(
            'ep',
            'Energy',
            trait_type='gauge',
            min=0,
            max=100,
            base=100,
            rate=0.1
        )
        self.traits.add(
            "evasion",
            trait_type="counter",
            min=0,
            max=100,
            base=0,
            stat="agi"
        )

    def at_pre_move(self, destination, **kwargs):
        if statuses := self.tags.get(_IMMOBILE, category='status', return_list=True):
            self.msg(
                f"You can't move while you're {iter_to_str(sorted(statuses), endsep='or')}."
            )
            return False 
        
        if self.in_combat:
            self.msg("You can't leave while in combat.")
            return False 
        
        return super().at_pre_move(destination, **kwargs)

    def at_post_move(self, source_location, **kwargs):
        super().at_post_move(source_location, **kwargs)

        if self.account and (settings := self.account.db.settings):
            if settings.get('auto prompt'):
                status = self.get_display_status(self)
                self.msg(prompt=status)
            
    def at_damage(self, attacker, damage, damage_type=None):
        damage -= self.defense(damage_type)
        self.traits.hp.current -= max(damage, 0)
        self.msg(f"You take {damage} damage {f'as |w{damage_type}|n' if damage_type else ''} from |r{attacker.get_display_name(self)}|n!")
        attacker.msg(f"You deal {damage} damage {f'as |w{damage_type}|n' if damage_type else ''} from |r{self.get_display_name(attacker)}|n.")

        if self.traits.hp.value <= 0:
            self.tags.add('unconscious', category="status")
            self.tags.add('lying down', category='status')
            self.msg(
                "You fall unconscious. You can |wrespawn|n or wait to be |wrevived|n."
            )
            self.traits.hp.rate = 0 
            if self.in_combat:
                combat = self.location.scripts.get('combat')[0]
                combat.remove_combatant(self)

    def at_emote(self, message, **kwargs):
        if not message or not self.location:
            return 
        if message[-1] not in punctuation:
            message += '.'
        if kwargs.get('prefix', True) and not message.startswith('$You()'):
            message = f'$You() {message}'
        mapping = kwargs.get('mapping', None)

        self.location.msg_contents(text=message, from_obj=self, mapping=mapping)

    def at_wield(self, weapon, **kwargs):
        wielded = self.attributes.get("_wielded", {})
        if wielded:
            wielded.deserialize()

        free = self.free_hands

        if hand := kwargs.get('hand'):
            if hand not in free:
                if not (weap := wielded.get(hand)):
                    self.msg(f"You do not have a free {hand}.")
                else:
                    self.msg(
                        f'You are already wielding {weap.get_display_name(self)} in your {hand}.'
                    )
                return 
        elif not free:
            self.msg("Your hands are full.")
            return 

        if weapon.tags.has('two_handed', category='wielded'):
            if len(free) < 2:
                self.msg(
                    f"You need two free hands to wield {weap.get_display_name(self)}."
                )
                return 
            hands = free[:2]
            for hand in hands:
                wielded[hand] = weapon
        else:
            if main_hand := self.db.handedness:
                hand = main_hand if main_hand in free else free[0]
            else:
                hand = free[0]

            hands = [hand]
            wielded[hand] = weapon 
        self.db._wielded = wielded 
        return hands 

    def at_unwield(self, weapon, **kwargs):
        wielded = self.attributes.get("_wielded", {})
        if wielded:
            wielded.deserialize()
        
        if weapon not in wielded.values():
            self.msg("You are not wielding that.")
            return 
        
        freed = []
        for hand, weap in wielded.items():
            if weap == weapon:
                wielded[hand] = None 
                freed.append(hand)
        
        self.db._wielded = wielded

        return freed 

    def use_skill(self, skill_name, *args, **kwargs):
        if not skill_name:
            return 1
        
        if not (skill_trait := self.traits.get(skill_name)):
            return 0
        
        stat_bonus = 0 
        if stat := getattr(skill_trait, "stat", None):
            stat_bonus = self.attributes.get(stat, 0)
        
        return skill_trait.value + stat_bonus 

    def get_display_status(self, looker, **kwargs):
        chunks = []
        if looker != self:
            chunks.append(self.get_display_name(looker, **kwargs))
        
        chunks.append(
            f"Health {self.traits.hp.percent()} : Energy {self.traits.ep.percent()} : Focus {self.traits.fp.percent()}"
        )

        if status_tags := self.tags.get(category='status', return_list=True):
            chunks.append(iter_to_str(status_tags))

        if looker == self:
            all_cooldowns = [
                (key, self.cooldowns.time_left(key, use_int=True))
                for key in self.cooldowns.all
            ]
            all_cooldowns = [f"{c[0]} ({c[1]}s)" for c in all_cooldowns if c[1]]
            if all_cooldowns:
                chunks.append(
                    f"Cooldowns: {iter_to_str(all_cooldowns, endsep=',')}"
                )

            return ' - '.join(chunks)

    def at_character_arrive(self, char, **kwargs):
        pass

    def at_character_depart(self, char, destination, **kwargs):
        pass

    def revive(self, reviver, **kwargs):
        if self.tags.has('unconscious'):
            self.tags.remove('unconscious')
            self.tags.remove('lying down')

            self.traits.hp.current = self.traits.hp.current.max // 5
            self.msg(prompt=self.get_display_status(self))
            self.traits.hp.rate = 0.1



class PlayerCharacter(Character):
    def at_object_creation(self):
        super().at_object_creation()

        self.db._wielded = {
            'left': None,
            'right': None
        }
    
    def get_display_name(self, looker, **kwargs):
        name = super().get_display_name(looker)
        if looker == self:
            return f"|c{name}|n"
        return f"|g{name}|n"

    def at_pre_object_receive(self, object, source_loc, **kwargs):
        if len([obj for obj in self.contents if not obj.db.worn]) > _MAX_CAPACITY:
            self.msg("You can't carry anymore.")
            source_loc.msg(f"{self.get_display_name(source_loc)} can't carry any more.")
            return False
        return super().at_pre_object_receive(object, source_loc, **kwargs)

    def at_damage(self, attacker, damage, damage_type=None):
        super().at_damage(attacker, damage, damage_type=damage_type)
        if self.traits.hp.value < 50:
            status = self.get_display_status(self)
            self.msg(prompt=status)
        
    def attack(self, target, weapon, **kwargs):
        if not self.in_combat:
            return 
        
        if self.db.fleeing:
            return 

        if not (hasattr(weapon, "at_pre_attack") and hasattr(weapon, "at_attack")):
            self.msg(
                f"You cannot attack with {weapon.get_numbered_name(1, self)}."
            )
            return 
        if not weapon.at_pre_attack(self):
            return 

        if not target:
            if not (target := self.db.combat_target):
                self.msg("You cannot attack nothing.")
                return 

        if target.location != self.location:
            self.msg("You can't find your target.")
            return 

        weapon.at_attack(self, target)

        status = self.get_display_status(self)
        self.msg(prompt=status)

        if self.account and (settings := self.account.db.settings):
            if settings.get('auto attack') and (speed := weapon.speed):
                delay(speed + 1, self.attack, None, weapon, persistent=True)

    def respawn(self):
        self.tags.remove("unconscious", category="status")
        self.tags.remove("lying down", category="status")
        self.traits.hp.reset()
        self.traits.hp.rate = 0.1
        self.move_to(self.home)
        self.msg(prompt=self.get_display_status(self))


class NPC(Character):
    name_color = AttributeProperty("w")

    @property
    def speed(self):
        weapon = self.db.natural_weapon 
        if not weapon:
            return 10 
        return weapon.get('speed', 10)

    def get_display_name(self, looker, **kwargs):
        name = super().get_display_name(looker, **kwargs)
        return f"|{self.name_color}{name}|n"
    
    def at_character_arrive(self, char, **kwargs):
        if 'aggressive' in self.attributes.get('react_as', ""):
            delay(1, self.enter_combat, char)

    def at_character_depart(self, char, destination, **kwargs):
        if char == self.db.following:
            exits = [
                x
                for x in self.location.contents_get(content_type='exit')
                if x.destination == destination
            ]
            if exits:
                self.execute_cmd(exits[0].name)
        
    def at_damage(self, attacker, damage, damage_type=None):
        super().at_damage(attacker, damage, damage_type=damage_type)

        if self.traits.hp.value <= 0:
            if combat := self.location.scripts.get("combat"):
                combat = combat[0]
                if not combat.remove_combatant(self):
                    return 
                
                objs = spawn(*list(self.db.drops))
                for obj in objs:
                    obj.location = self.location 

                self.delete()
                return 

        if 'timid' in self.attributes.get('react_as', ''):
            self.at_emote("flees!")
            self.db.fleeing = True 
            if combat := self.location.scripts.get("combat"):
                combat = combat[0]
                if not combat.remove_combatant(self):
                    return 

            if randint(0, 1):
                self.move_to(None)
                self.delete()
            else:
                flee_dir = choice(self.location.contents_get(content_type='exit'))
                flee_dir.at_traverse(self, flee_dir.destination)
            return 

        threshold = self.attributes.get("flee_at", 25)
        if self.traits.hp.value <= threshold:
            self.execute_cmd("flee")

        if not self.db.combat_target:
            self.enter_combat(attacker)
        else:
            self.db.combat_target = attacker 

    def enter_combat(self, target, **kwargs):
        if weapons := self.wielding:
            weapon = weapons[0]
        else:
            weapon = self 
        
        self.at_emote("$conj(charges) at {target}!", 
        mapping={"target": taret}
        )
        location = self.location 

        if not (combat := location.scripts.get("combat")):
            from typeclasses.scripts import CombatScript 

            location.scripts.add(CombatScript, key="combat")
            combat = location.scripts.get("combat")
        combat = combat[0]

        self.db.combat_target = target 

        if not combat.add_combatant(self, enemy=target):
            return 
        
        self.attack(target, weapon)

    def attack(self, target, weapon, **kwargs):
        if not self.in_combat or self.db.fleeing:
            return 

        if not target:
            if not (target := self.db.combat_target):
                return 
        
        if self.location != target.location:
            return 

        if not (hasattr(weapon, 'at_pre_attack') and hasattr(weapon, 'at_attack')):
            return 
        if not weapon.at_pre_attack(self):
            return 
        
        weapon.at_attack(self, target)
        
        delay(weapon.speed + 1, self.attack, None, weapon, persistent=True)

    def at_pre_attack(self, wielder, **kwargs):
        if self != wielder:
            return 
        if not (weapon := self.db.natural_weapon):
            return
        if self.traits.ep.value < weapon.get('energy_cost', 5):
            return False 
        
        if not wielder.cooldowns.ready('attack'):
            return False 

        return True 

    def at_attack(self, wielder, target, **kwargs):
        weapon = self.db.natural_weapon 
        damage = weapon.get('damage', 0)
        speed = weapon.get('speed', 0)

        result = self.use_skill(weapon.get('skill'), speed=speed)

        damage = damage * result 

        self.traits.ep.current -= weapon.get('energy_cost', 5)
        if not damage:
            self.at_emote(
                f"$conj(swings) $pron(your) {weapon.get('name')} at $you(target), but $conj(misses).",
                mapping={'target': target}
            )
        else:
            verb = weapon.get('damage_type', 'hits')
            wielder.at_emote(
                f"$conj({verb}) $you(target) with $pron(your) {weapon.gete('name')}.",
                mapping={'target': target}
            )
        wielder.msg(f"[ Cooldown: {speed} seconds ]")
        wielder.cooldowns.add('attack', speed)