from .audio import *
from .gamevisuals import *


# MAINWIDGET FOR TESTING GAME VISUALS INDEPENDENTLY OF THE ENTIRE GAME
class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()
        self.anim_group = AnimGroup()
        self.game_display = GameDisplay()
        self.anim_group.add(self.game_display)

        self.playing = False

        self.canvas.add(self.anim_group)

        self.label = topleft_label()
        self.add_widget(self.label)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == 'p':
            pass

        if keycode[1] == 'z':
            pass

    def on_key_up(self, keycode):
        # button up
        pass

    def on_update(self) :
        self.label.text = "Welcome to Beat Runner\n"
        self.anim_group.on_update()