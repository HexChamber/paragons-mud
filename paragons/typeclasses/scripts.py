"""
Scripts

Scripts are powerful jacks-of-all-trades. They have no in-game
existence and can be used to represent persistent game systems in some
circumstances. Scripts can also have a time component that allows them
to "fire" regularly or a limited number of times.

There is generally no "tree" of Scripts inheriting from each other.
Rather, each script tends to inherit from the base Script class and
just overloads its hooks to have it perform its function.

"""
from random import randint, choice
from evennia.utils import make_iter, logger 
from evennia.scripts.scripts import DefaultScript
from evennia.prototypes.prototypes import PROTOTYPE_TAG_CATEGORY
from evennia.prototypes.spawner import spawn

class Script(DefaultScript):
    """
    A script type is customized by redefining some or all of its hook
    methods and variables.

    * available properties

     key (string) - name of object
     name (string)- same as key
     aliases (list of strings) - aliases to the object. Will be saved
              to database as AliasDB entries but returned as strings.
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
     date_created (string) - time stamp of object creation
     permissions (list of strings) - list of permission strings

     desc (string)      - optional description of script, shown in listings
     obj (Object)       - optional object that this script is connected to
                          and acts on (set automatically by obj.scripts.add())
     interval (int)     - how often script should run, in seconds. <0 turns
                          off ticker
     start_delay (bool) - if the script should start repeating right away or
                          wait self.interval seconds
     repeats (int)      - how many times the script should repeat before
                          stopping. 0 means infinite repeats
     persistent (bool)  - if script should survive a server shutdown or not
     is_active (bool)   - if script is currently running

    * Handlers

     locks - lock-handler: use locks.add() to add new lock strings
     db - attribute-handler: store/retrieve database attributes on this
                        self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not
                        create a database entry when storing data

    * Helper methods

     start() - start script (this usually happens automatically at creation
               and obj.script.add() etc)
     stop()  - stop script, and delete it
     pause() - put the script on hold, until unpause() is called. If script
               is persistent, the pause state will survive a shutdown.
     unpause() - restart a previously paused script. The script will continue
                 from the paused timer (but at_start() will be called).
     time_until_next_repeat() - if a timed script (interval>0), returns time
                 until next tick

    * Hook methods (should also include self as the first argument):

     at_script_creation() - called only once, when an object of this
                            class is first created.
     is_valid() - is called to check if the script is valid to be running
                  at the current time. If is_valid() returns False, the running
                  script is stopped and removed from the game. You can use this
                  to check state changes (i.e. an script tracking some combat
                  stats at regular intervals is only valid to run while there is
                  actual combat going on).
      at_start() - Called every time the script is started, which for persistent
                  scripts is at least once every server start. Note that this is
                  unaffected by self.delay_start, which only delays the first
                  call to at_repeat().
      at_repeat() - Called every self.interval seconds. It will be called
                  immediately upon launch unless self.delay_start is True, which
                  will delay the first call of this method by self.interval
                  seconds. If self.interval==0, this method will never
                  be called.
      at_stop() - Called as the script object is stopped and is about to be
                  removed from the game, e.g. because is_valid() returned False.
      at_server_reload() - Called when server reloads. Can be used to
                  save temporary variables you want should survive a reload.
      at_server_shutdown() - called at a full server shutdown.

    """

    pass


class RestockScript(Script):
  pass



# class CombatScript(Script):
#   def teams(self):
#     if not self.ndb.teams:
#       if teams := self.db.teams:
#         self.ndb.teams = teams.deserialize()

#     return self.ndb.teams 

#   @property
#   def fighters(self):
#     a, b = self.teams 
#     return a + b 

#   @property 
#   def active(self):
#     return [
#       obj 
#       for obj in self.fighters
#       if not any(obj.tags.has(['unconscious', 'dead', 'defeated']))
#     ]

#   def at_script_creation(self):
#     self.db.teams = [[], [],]
  
#   def get_team(self, combatant):
    
class CombatScript(Script):
    @property
    def teams(self):
        if not self.ndb.teams:
            if teams := self.db.teams:
                self.ndb.teams = teams.deserialize()

        return self.ndb.teams

    @property
    def fighters(self):
        a, b = self.teams
        return a + b 

    @property
    def active(self):
        return [
            obj 
            for obj in self.fighters
            if not any(obj.tags.has(['unconscious', 'dead', 'defeated']))
        ]

    def at_script_creation(self):
        self.db.teams = [[], []]

    def get_team(self, combatant):
        for i, team in enumerate(self.teams):
            if combatant in team:
                return i
        return None 

    def add_combatant(self, combatant, ally=None, enemy=None, **kwargs):
        if combatant in self.fighters:
            return True 

        if not (ally or enemy):
            return False 

        if ally and (team := self.get_team(ally)):
            self.db.teams[team].append(combatant)

            del self.ndb.teams
            return True 
        if enemy and (team := self.get_team(enemy)):
            team -= 1

            self.db.teams[team].append(combatant)
            del self.ndb.teams 
            return True 
        
        if enemy and not self.fighters:
            self.db.teams = [[combatant], [enemy]]
            del self.ndb.teams 
            return True 
        
        return False 
    
    def remove_combatant(self, combatant, **kwargs):
        team = self.get_team(combatant)
        if team is None:
            return True 
        
        self.db.teams[team].remove(combatant)
        del self.ndb.teams 

        if exp := combatant.db.exp_reward:
            for obj in self.db.teams[team - 1]:
                if obj.db.exp:
                    obj.msg(f"You gain {exp} XP.")
                    obj.db.exp += exp
        self.check_victory()

        del combatant.db.combat_target 
        return True 
    
    def check_victory(self):
        if not (active_fighters := self.active):
            self.delete()
            return 
        
        team_a, team_b = [
            [obj for obj in team if obj in active_fighters] for team in self.db.teams
        ]
        if team_a and team_b:
            return 
        if not team_a and not team_b:
            self.delete()
            return 
        
        for obj in active_fighters:
            del obj.db.combat_target
            obj.msg("The fight is over.")
        
        self.delete()


class RestockScript(Script):
    def at_script_creation(self):
        self.interval = 3600

    def at_repeat(self):
        if not (storage := self.obj.db.storage):
            return 
        if not (inventory := self.obj.db.inventory):
            return 

        for prototype, max_count in inventory:
            in_stock = [
                obj
                for obj in storage.contents
                if obj.tags.has(prototype, category=PROTOTYPE_TAG_CATEGORY)
            ]
            if len(in_stock) >= max_count:
                continue 
            if new_stock := randint(0, 3):
                new_stock = min(new_stock, max_count - len(in_stock))

                objs = spawn(*[prototype] * new_stock)

                for obj in objs:
                    obj.db.value = obj.db.value or 1 
                    self.obj.add_stock(obj)
                    