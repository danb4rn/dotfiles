from libqtile import layout
from libqtile.config import Match

layouts = [
    layout.MonadTall(margin=20, single_margin=70,
                     border_width=2, 
                     border_focus='#5294e2',
                     border_normal='#2c5380'),

    #layout.Columns(border_focus_stack='#d75f5f'),
    #layout.Max(),
    # Try more layouts by unleashing below layouts.
    # layout.Stack(num_stacks=2),
    layout.Bsp(margin=20, border_width=2,
                     margin_on_single=70,
                     border_on_single=True, 
                     border_focus='#5294e2',
                     border_normal='#2c5380'),
    layout.Matrix(margin=20, border_width=2, 
                     border_focus='#5294e2',
                     border_normal='#2c5380'),

    # layout.MonadTall(),
    # layout.MonadWide(),
    # layout.RatioTile(),
    # layout.Tile(),
    # layout.TreeTab(),
    # layout.VerticalTile(),
    # layout.Zoomy(),
]

floating_layout = layout.Floating(float_rules=[
    # Run the utility of `xprop` to see the wm class and name of an X client.
    *layout.Floating.default_float_rules,
    Match(wm_class='confirmreset'),  # gitk
    Match(wm_class='makebranch'),  # gitk
    Match(wm_class='maketag'),  # gitk
    Match(wm_class='ssh-askpass'),  # ssh-askpass
    Match(title='branchdialog'),  # gitk
    Match(title='pinentry'),  # GPG key password entry
])
