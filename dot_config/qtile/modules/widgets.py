from libqtile import widget
from libqtile import qtile

colors = [["#282c34", "#282c34"],
          ["#1c1f24", "#1c1f24"],
          ["#eceff4", "#eceff4"],
          ["#bf616a", "#bf616a"],
          ["#a3be8c", "#a3be8c"],
          ["#d08770", "#d08770"],
          ["#5e81ac", "#5e81ac"],
          ["#b48ead", "#b48ead"],
          ["#88c0d0", "#88c0d0"],
          ["#a9a1e1", "#a9a1e1"]]


widget_defaults = dict(
    font="Ubuntu Bold",
    fontsize = 10,
    padding = 2,
    background=colors[2]
)
extension_defaults = widget_defaults.copy()
extension_defaults = widget_defaults.copy()
class MyVolume(widget.Volume):
    def _configure(self, qtile, bar):
        widget.Volume._configure(self, qtile, bar)
        self.volume = self.get_volume()
        if self.volume <= 0:
            self.text = ''
        elif self.volume <= 15:
            self.text = ''
        elif self.volume < 50:
            self.text = ''
        else:
            self.text = ''
        # drawing here crashes Wayland

    def _update_drawer(self, wob=False):
        if self.volume <= 0:
            self.text = ''
        elif self.volume <= 15:
            self.text = ''
        elif self.volume < 50:
            self.text = ''
        else:
            self.text = ''
        self.draw()

        if wob:
            with open(self.wob, 'a') as f:
                f.write(str(self.volume) + "\n")

volume = MyVolume(
    fontsize=18,
    font='Font Awesome 5 Free',
    foreground=colors[4],
    background='#2f343f',
    mouse_callbacks = {'Button1': lambda: qtile.cmd_spawn("pavucontrol")}
)
