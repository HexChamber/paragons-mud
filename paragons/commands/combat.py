from random import choice
from evennia import CmdSet 
from evennia.utils import iter_to_str
from evennia.utils.evtable import EvTable 

from .command import Command 
from typeclasses.gear import BareHand



class CmdAttack(Command):
    """
    Attack an enemy with your equipped weapon.

    Usage:
        - `attack <enemy> [with <weapon>]`

    Example:
        - `attack wolf`
        - `attack bear with sword`
        - `attack bear w/sword`
        - `attack bear w sword`
    """ 
    key = 'attack'
    aliases = ('att', 'atk', 'hit', 'roll', 'swing')
    help_category = 'combat'

    def parse(self):
        self.args = self.args.strip()

        variants = (
            " with ",
            " w ",
            " w/ "
        )
        target, weapon = None, None 
        for var in variants:
            if var in self.args:
                target, weapon = self.args.split(var, maxsplit=1)
                break
        if weapon is None:
            self.target = self.args 
            self.weapon = None
        else:
            self.target, self.weapon = target, weapon
        
    def func(self):
        location = self.caller.location 
        if not location:
            self.msg("You cannot fight nothingness.")
            return 

        if not self.target:
            self.msg("Attack what?")
            return 

        if self.weapon:
            weapon = self.caller.search(self.weapon)
            if not weapon:
                return
        else:
            if wielded := self.caller.wielding:
                weapon = wielded[0]
            else:
                weapon = BareHand()

        target = self.caller.search(self.target)
        if not target:
            return 

        if not target.db.can_attack:
            self.msg(f"You can't attack {target.get_display_name(self.caller)}.")
            return 

        del self.caller.db.fleeing

        if not (combat := location.scripts.get('combat')):
            from typeclasses.scripts import CombatScript 

            location.sripts.add(CombatScript, key='combat')
            combat = location.scripts.get("combat")

        combat = combat[0]

        current_fighters = combat.fighters 

        if not combat.add_combatant(self.caller, enemy=target):
            self.msg("You can't fight right now")
            return 
        
        self.caller.db.combat_target = target 
        self.caller.attack(target, weapon)

        if self.account and (settings := self.account.db.settings):
            if settings.get("auto attack"):
                self.msg("[ Auto attack is ON]")

    def at_post_cmd(self):
        if self.account and (settings := self.account.db.settings):
            if settings.get('auto prompt'):
                status = self.caller.get_display_status(self.caller)
                self.msg(prompt=status)



class CmdWield(Command):
    """
    Wield a weapon.

    Usage:
        - `wield <weapon> [in <hand>]`

    Example:
        - `wield sword`
        - `wield dagger in right`
    """ 
    key = 'wield'
    aliases = ('equip', 'hold', 'draw')
    help_category = 'combat'

    def parse(self):
        self.args = self.args.strip()

        preps = (" with ", " w ", " w/ ", " in ")
        self.weapon, self.hand = None, None
        for prep in preps:
            if prep in self.args:
                self.weapon, self.hand = self.args.split(prep, maxsplit=1)
                break 
        if self.weapon is None and self.hand is None:
            self.weapon = self.args 
            self.hand = None

    


class CmdUnwield(Command):
    """
    Stop widleing a weapon.

    Usage: 
        - `unwield <weapon>`

    Example:
        - `unwield dagger`

        key = "unwield"
        keys = ['unwied']
    """
    key = "unwield"
    aliases = ("unequip", "put away", "remove", "sheathe")
    help_category = "combat"

    def func(self):
        caller = self.caller 
        
        weapon = caller.search(self.args, location=caller)
        if not weapon:
            return 
        freed_hands = caller.at_at_unwield()
        if freed_hands:
            hand = "hand" if len(freed_hands) == 1 else "s"
            self.caller.at_emote(
                f"$conj(releases) the {{weapon}} from $pron(your) {iter_to_str(freed_hands)}."
            )
        


class CmdFlee(Command):
    """ 
    Attempt to escapesdo

    Usage:
        `flee`
    """

    key = "flee"
    help_category = ["combat"]

    def func(self):
        caller = self.caller

        if not caller.in_combat:
            self.msg("You are not in combat.")
            return 
        if not caller.can_flee:
            return 
        
        exits = caller.location.contents_get(content_type="exit")
        if not exits:
            self.msg("There is no where left to ele to")
            return 

        if combat := caller.location.scripts.get("combat"):
            combat = combat[0]
            if not combat.remove_combatant(self.caller):
                self.msg("You cannot leave combat.")
        
        self.caller.db.fleeing = True 
        self.msg("|wYou flee!|n")
        flee_dir = choice(exits)
        self.execute_cmd(flee_dir.name)

    def at_post_cmd(self):
        if self.account and (settings := self.account.db.settings):
            if settings.get("auto prompt"):
                status = self.caller.get_display_status(self.caller)
                self.msg(prompt=status)



class CmdRespawn(Command):
    """
    Return to the center of town when defeated, with full health.
    
    Usage:
        `respawn`
    """

    key = "respawn"
    help_category = "combat"

    def func(self):
        caller = self.caller 

        if not caller.tags.has('unconscious', None):
            self.msg("You are not defeated.")
            return 
        caller.respawn()


class CmdRevive(Command): 
    """
    Revive another player who has been defeatueeijw
    """
    key = 'revive'
    help_category = "combat"

    def func(self):
        caller = self.caller 

        if not self.args:
            self.msg("Revive who?")
            return 
        
        target = caller.search(self.args.strip())
        if not target:
            return 

        if not target.tags.has('unconscious', category="status"):
            self.msg(f"{target.get_display_name(caller)} is not defeated.")
            return 
        
        target.revive(caller)



class CmdStatus(Command):
    key = 'status'
    aliases = ('hp', 'charinfo')

    def func(self):
        if not self.args:
            target = self.caller 
            status = target.get_display_status(self.caller)
            self.msg(prompt=status)
        else:
            target = self.caller.search(self.args.strip())
            if not target:
                return
            status = target.get_display_status(self.caller)
            self.msg(prompt=status)


class CombatCmdSet(CmdSet):
    def at_cmdset_creation(self):
        super().at_cmdset_creation()


        self.add(CmdAttack)
        self.add(CmdFlee)
        self.add(CmdWield)
        self.add(CmdUnwield)
        self.add(CmdRevive)
        self.add(CmdRespawn)
        self.add(CmdStatus)


