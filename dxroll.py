# IMPORTS
# -- Textual
from textual.app import App
from textual.binding import Binding
from textual.containers import ScrollableContainer, Grid
from textual.widgets import Header, Footer,Static, Select, LoadingIndicator
from textual.widget import Widget
from textual.reactive import reactive
from textual.screen import ModalScreen
# -- Std. libs
import asyncio
import random
# ----------------

# CONSTANTS 
MAX_DICE_COUNT = 10
DICE_VALUE_DICT = {
    "D4": ["1","2","3","4"],
    "D6": ["1","2","3","4","5","6"],
    "D8": ["1","2","3","4","5","6","7","8"],
    "D%": ["00","10","20","30","40","50","60","80","90"],
    "D10": ["0","1","2","3","4","5","6","7","8","9"],
    "D12": ["1","2","3","4","5","6","7","8","9","10","11","12"],
    "D20": ["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20"]
}
APPLICATION_TITLE = "dxroll 🧙🏼‍♂️"
APPLICATION_SUB_TITLE = "v0.0.1"
# ----------------

# ROLL OUTCOME DISPLAY
class RollOutcomeDisplay(Widget):
    roll = reactive(0)
    outcome = reactive(0)

    def render(self):
        return f"☄️  Roll: {self.roll} | ⭐ Outcome: {self.outcome}"

# GLOBAL DISPLAY
class GlobalDisplay(Widget):
    modifier = reactive(0)
    roll = reactive(0)
    outcome = reactive(0)

    def render(self):
        return f"🌍 | Global Modifier: {'+' if self.modifier > -1 else ''}{self.modifier} | Global Roll: {self.roll} | Global Outcome: {self.outcome}"

# GLOBAL CH MOD SCREEN
class GlobalModScreen(ModalScreen[int]):
    def compose(self):
        yield Grid(
            Select(
                [
                    ("-5",-5),
                    ("-4",-4),
                    ("-3",-3),
                    ("-2",-2),
                    ("-1",-1),
                    ("+0",0),
                    ("+1",1),
                    ("+2",2),
                    ("+3",3),
                    ("+4",4),
                    ("+5",5),
                    ("+6",6),
                    ("+7",7),
                    ("+8",8),
                    ("+9",9),
                    ("+10",10),
                    ("+11",11),
                    ("+12",12),
                    ("+13",13),
                    ("+14",14),
                    ("+15",15)
                ],
                prompt="Select dice modifier...",
                id="global-mod-select",
                allow_blank=False,
                value=self.app.global_modifier
            ),
            id="dialog"
        )

    def on_mount(self):
        self.query_one('#dialog').border_title = "Global modifier"
        
    def on_select_changed(self, event: Select.Changed):
        if (event.select.id == 'global-mod-select'):
            self.dismiss(event.select.value)

# DICE WIDGET
class Dice(Static):

    type = reactive('')
    modifier = reactive(0)
    roll = reactive(0)
    outcome = reactive(0)

    def compose(self):
        yield Select(
            [
                ("D4","D4"),
                ("D6","D6"),
                ("D8","D8"),
                ("D%","D%"),
                ("D10","D10"),
                ("D12","D12"),
                ("D20","D20")
            ],
            prompt="Select dice type...",
            id="dice-type-select",
            allow_blank=False
        )
        yield Select(
            [
                ("-5",-5),
                ("-4",-4),
                ("-3",-3),
                ("-2",-2),
                ("-1",-1),
                ("+0",0),
                ("+1",1),
                ("+2",2),
                ("+3",3),
                ("+4",4),
                ("+5",5),
                ("+6",6),
                ("+7",7),
                ("+8",8),
                ("+9",9),
                ("+10",10),
                ("+11",11),
                ("+12",12),
                ("+13",13),
                ("+14",14),
                ("+15",15)
            ],
            prompt="Select dice modifier...",
            id="dice-mod-select",
            allow_blank=False,
            value=0
        )
        yield LoadingIndicator(classes='hidden')
        yield RollOutcomeDisplay(classes='hidden', id='roll-outcome-display')

    def on_select_changed(self, event: Select.Changed):
        if(event.select.id == 'dice-type-select'):
            self.type = event.select.value
            self.border_title = f"🎲 { self.type}"
            event.select.blur()
            event.select.disabled = True
            event.select.expanded = False
            dice_mod_select = self.query_one('#dice-mod-select')
            dice_mod_select.focus()
            dice_mod_select.expanded = True
        elif (event.select.id == 'dice-mod-select'):
            self.modifier = event.select.value
            self.border_title = f'🎲 {self.type} ({"+" if self.modifier > -1 else ""}{str(self.modifier)})' 
            event.select.blur()
            event.select.disabled = True
            event.select.expanded = False
            self.query_one('#dice-type-select').add_class('hidden')
            event.select.add_class('hidden')

# ----------------

# MAIN APP
class Main(App):

    CSS_PATH = "./dxroll.tcss"
    TITLE = APPLICATION_TITLE
    SUB_TITLE = APPLICATION_SUB_TITLE

    BINDINGS = [
        Binding("q", "exit()", "Exit", show=True, priority=False, key_display="Q"),
        Binding("+", "add_dice()", "Add", show=True, priority=False, key_display="+"),
        Binding("-", "remove_dice()", "Remove", show=True, priority=False, key_display="-"),
        Binding("up", "navigate_prev()", "Prev", show=True, priority=False, key_display="↑"),
        Binding("down", "navigate_next()", "Next", show=True, priority=False, key_display="↓"),
        Binding("c", "change_mod()", "Ch. mod.", show=True, priority=False, key_display="C"),
        Binding("x", "roll_dice()", "Roll", show=True, priority=False, key_display="X"),
        Binding("C", "change_global_mod()", "Ch. global mod.", show=True, priority=False, key_display="SHIFT+C"),
        Binding("X", "roll_all_dice()", "Roll all", show=True, priority=False, key_display="SHIFT+X"),
    ]

    global_roll = reactive(0)
    global_outcome = reactive(0)
    global_modifier = reactive(0)
    
    def compose(self):
        yield Header()
        yield Footer()
        yield GlobalDisplay(id="global-display")
        yield ScrollableContainer(id="dice-container")

    async def action_add_dice(self):
        dice = self.query("Dice")
        if len(dice) < MAX_DICE_COUNT:
            if len(dice) > 0:
                active_dice = self.query_one(".active")
                if active_dice.get_child_by_id('dice-type-select').expanded or active_dice.get_child_by_id('dice-mod-select').expanded:
                    return
            for d in dice:
                d.remove_class("active")
            new_dice = Dice()
            await self.query_one("#dice-container").mount(new_dice)
            new_dice.add_class("active")
            new_dice.scroll_visible()
            dice_type_select = new_dice.get_child_by_id('dice-type-select')
            dice_type_select.disabled = False
            dice_type_select.focus()
            dice_type_select.expanded = True

    def action_remove_dice(self):
        dice = self.query("Dice")
        if(dice):
            active_dice = dice.filter(".active").last()
            if active_dice.get_child_by_id('dice-type-select').expanded or active_dice.get_child_by_id('dice-mod-select').expanded:
                    return
            active_dice_idx = list(dice).index(active_dice)
            if len(dice) > 1 and active_dice_idx == len(dice)-1:
                active_dice.remove_class("active")
                active_dice.remove()
                dice[active_dice_idx-1].add_class("active")
            elif len(dice) > 1 and active_dice_idx == 0:
                active_dice.remove_class("active")
                active_dice.remove()
                dice[active_dice_idx+1].add_class("active")
            elif len(dice) > 1 and active_dice_idx > 0 and active_dice_idx < len(dice)-1:
                active_dice.remove_class("active")
                active_dice.remove()
                dice[active_dice_idx+1].add_class("active")
            else:
                active_dice.remove_class("active")
                active_dice.remove()

    def action_navigate_prev(self):
        dice = self.query("Dice")
        if(dice):
            active_dice = dice.filter(".active").last()
            active_dice_idx = list(dice).index(active_dice)
            if len(dice) > 1 and not active_dice_idx == 0:
                active_dice.remove_class("active")
                dice[active_dice_idx - 1].add_class("active")
                dice[active_dice_idx - 1].scroll_visible()
    
    def action_navigate_next(self):
        dice = self.query("Dice")
        if(dice):
            active_dice = dice.filter(".active").last()
            active_dice_idx = list(dice).index(active_dice)
            if len(dice) > 1 and not active_dice_idx == len(dice)-1:
                active_dice.remove_class("active")
                dice[active_dice_idx + 1].add_class("active")
                dice[active_dice_idx + 1].scroll_visible()

    def action_change_mod(self): 
        if len(self.query('Dice')) > 0:
            dice_mod_select = self.query_one('.active #dice-mod-select')
            dice_type_select = self.query_one('.active #dice-type-select')
            roll_outcome_display = self.query_one('.active #roll-outcome-display')
            roll_outcome_display.add_class('hidden')
            dice_mod_select.remove_class('hidden')
            dice_type_select.remove_class('hidden')
            if dice_mod_select.expanded or dice_type_select.expanded:
                pass
            else:
                dice_mod_select.disabled = False
                dice_mod_select.focus()
                dice_mod_select.expanded = True   

    async def action_roll_dice(self):
        if len(self.query('Dice')) > 0:
            active_loading_indicator = self.query_one('.active LoadingIndicator')
            if 'hidden' in active_loading_indicator.classes:
                active_dice = self.query_one('.active')
                active_dice.get_child_by_id('roll-outcome-display').add_class("hidden")
                active_loading_indicator.remove_class('hidden')
                roll = random.choice(DICE_VALUE_DICT[active_dice.type])
                active_dice.roll = active_dice.get_child_by_id('roll-outcome-display').roll = roll
                outcome = int(roll) + active_dice.modifier
                active_dice.outcome = active_dice.get_child_by_id('roll-outcome-display').outcome = outcome
                await asyncio.sleep(0.5)
                active_loading_indicator.add_class('hidden')
                active_dice.get_child_by_id('roll-outcome-display').remove_class("hidden")
    
    def action_change_global_mod(self):
        def callback_change_global_mod(modifier):
            self.global_modifier = self.get_child_by_id('global-display').modifier = modifier
        self.push_screen(GlobalModScreen(), callback_change_global_mod)

    async def action_roll_all_dice(self):
        global_dice_list = self.query('Dice')
        if len(global_dice_list) > 0:
            active_dice = global_dice_list.filter(".active").last()
            if not(active_dice.get_child_by_id('dice-type-select').expanded or active_dice.get_child_by_id('dice-mod-select').expanded or isinstance(self.screen_stack[-1], GlobalModScreen)):
                global_roll_aggregated = 0
                for dice in global_dice_list:
                    self.title
                    dice.get_child_by_id('roll-outcome-display').add_class("hidden")
                    dice_loading_indicator = dice.query_one('LoadingIndicator')
                    dice_loading_indicator.remove_class('hidden')
                for dice in global_dice_list:
                    roll = random.choice(DICE_VALUE_DICT[dice.type])
                    dice.roll = dice.get_child_by_id('roll-outcome-display').roll = roll
                    outcome = int(roll) + dice.modifier
                    dice.outcome = dice.get_child_by_id('roll-outcome-display').outcome = outcome
                    global_roll_aggregated += int(roll)
                await asyncio.sleep(0.5)
                for dice in global_dice_list:
                    dice_loading_indicator = dice.query_one('LoadingIndicator')
                    dice_loading_indicator.add_class('hidden')
                    dice.get_child_by_id('roll-outcome-display').remove_class("hidden")
                global_outcome = global_roll_aggregated + self.global_modifier
                self.global_roll = self.get_child_by_id('global-display').roll = global_roll_aggregated
                self.global_outcome= self.get_child_by_id('global-display').outcome = global_outcome

    def action_exit(self):
        self.exit()
# ----------------

# APP
if __name__ == "__main__":
    app = Main()
    app.run()
# ----------------