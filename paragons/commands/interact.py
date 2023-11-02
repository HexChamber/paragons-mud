from evennia import CmdSet 
from evennia.utils import make_iter
from .command import Command 



class CmdGather(Command):
    """\ 
    Gather resources from the node in this location.
    """ 
    key = "gather"
    aliases = ("collect", "harvest", "mine", "hunt")

    def func(self):
        if not self.obj:
            return 
        
        try:
            self.obj.at_gather(self.caller)
        except AttributeError:
            self.msg("You cannot gather anything from that.")


class GatherCmdSet(CmdSet):
    key = "Gather CmdSet"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdGather)


class CmdEat(Command):
    """ 
    Eat something edible. 

    Usage: 
        - `eat <obj>`

    Example:
        - `eat apple`
    """
    key = "eat"
    aliases= ("drink", "consume", "absorb")

    def func(self):
        obj = self.caller.search(self.args.strip(), stacked=1)
        if not obj:
            return 
        
        obj = make_iter(obj)[0]

        if not obj.tags.has("edible"):
            self.msg("You cannot eat that.")
            return 
        
        energy = obj.attributes.get("energy", 0)
        self.caller.traits.ep.current += energy 
        self.caller.at_emote(
            f"$conj({self.cmdstring}) the {{target}}.",
            mapping={"target": obj}
        )
        obj.delete()


class InteractCmdSet(CmdSet):
    key = "Interact CmdSet"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdEat)
