#!/usr/bin/python3 -tt
import urwid
import gnupg
import subprocess
import time
from functools import partial

selected_keyid = None

def menu_button(caption, callback, user_args=None):
    button = urwid.Button(caption)
    urwid.connect_signal(button, 'click', callback, user_args=user_args)
    return urwid.AttrMap(button, None, focus_map='selected')

def sub_menu(caption, choices):
    contents = menu(caption, choices)
    def open_menu(button):
        return top.open_box(contents)
    return menu_button([caption, u'...'], open_menu)

def menu(title, choices):
    body = [urwid.Text(('title', title)), urwid.Divider()]
    body.extend(choices)
    return urwid.ListBox(urwid.SimpleFocusListWalker(body))

def item_chosen(button):
    response = urwid.Text([u'You chose ', button.label, u'\n'])
    done = menu_button(u'Ok', exit_program)
    top.open_box(urwid.Filler(urwid.Pile([response, done])))

def exit_program(button):
    raise urwid.ExitMainLoop()

def close_box(button, extra_arg=None):
    """Closes top box, unless passed an integer;
    then it closes that number of boxes"""
    if not isinstance(button, int):
        button = 1
    for i in range(button):
        top.close_box()

def algoname(pk):
    if pk['curve'] != '':
        return pk['curve']
    elif pk['algo'] == '1':
        return 'rsa' + pk['length']
    elif pk['algo'] == '17':
        return 'dsa' + pk['length']
    else:
        return 'algo' + pk['algo'] + '-' + pk['length']

def keyname(pk):
    return '%s (%s, %s)' % (pk['uids'][0],
            algoname(pk), pk['keyid'])

keyparams = {
        'DSA 3072':        'Key-Type: dsa\nKey-Length: 3072',
        'Ed25519':         'Key-Type: eddsa\nKey-Curve: Ed25519',
        'NIST P-521':      'Key-Type: ecdsa\nKey-Curve: NIST P-521',
        'brainpoolP512r1': 'Key-Type: ecdsa\nKey-Curve: brainpoolP512r1',
        'secp256k1':       'Key-Type: ecdsa\nKey-Curve: secp256k1',
        }

def use_new_key(mail, button):
    global selected_keyid
    selected_keyid = mail
    top.open_box(urwid.Filler(urwid.Pile([
        urwid.Text('Key %s created and selected' % mail),
        menu_button('OK', close_box, user_args=[4])
        ])))

def is_in_uids(mail):
    global uids
    for uid in uids:
        if mail in uid:
            return True
    return False

def validate_and_create_key(algo, name, mail, title, data, button):
    if len(name.edit_text) < 10:
        title.set_text(('err', "Name too short!"))
        return
    if len(mail.edit_text) < 10:
        title.set_text(('err', "Mail address too short!"))
        return
    if '@' not in mail.edit_text or '.' not in mail.edit_text:
        title.set_text(('err', "Invalid mail address format!"))
        return
    if is_in_uids(mail.edit_text):
        title.set_text(('err', "Mail address already in use!"
            "(Create key manually if you really want this)"))
        return
    keytype = keyparams[algo]
    params = """%s
Key-Usage: sign
Name-Real: %s
Name-Email: %s
%%no-protection
%%commit""" % (keytype, name.edit_text, mail.edit_text)
    title.set_text("Key generation running...")
    r = subprocess.run(["gpg", "--batch", "--generate-key"], input=params,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    if r.returncode == 0:
        title.set_text(('ok', "Key generation successful:"))
        data.set_text([r.stdout, ('err', r.stderr)])
        create_key_button.original_widget.set_label(('ok', "Use this key"))
        urwid.connect_signal(create_key_button.original_widget, 'click',
                use_new_key, user_args=[mail.edit_text])
    else:
        title.set_text(('err', "Key generation failed!"))
        data.set_text([r.stdout, ('err', r.stderr)])

def create_key_menu(button):
    global create_key_button
    name = urwid.Edit('> ')
    mail = urwid.Edit('> ')
    outtitle = urwid.Text(('special', ''))
    outdata = urwid.Text(('special', ''))
    create_key_button = menu_button('Create key!',
            validate_and_create_key,
            user_args=[button.label, name, mail, outtitle, outdata])
    m = menu("Create %s key" % button.label, [
            urwid.Text(('special', "Name (e.g. 'Hagrid Snakeoil Timestamper')")),
            name,
            urwid.Text(('special', "Email (e.g. 'hagrid@snakeoil.example')")),
            mail,
            urwid.Divider(),
            create_key_button,
            outtitle,
            outdata,
        ])
    top.open_box(m)

def crypto_options():
    items = [
        urwid.Text(('comment', "(Choose at random if you have no preference:)"))
    ]
    for i in keyparams.keys():
        items.append(menu_button(i, create_key_menu))
    return items

def gpg_menu(caption):
    gpg = gnupg.GPG()
    items = []
    global uids
    uids = []
    for pk in gpg.list_keys(secret=True):
        uids.extend(pk['uids'])
        if 'S' in pk['cap']:
            def key_chosen(keyid, button):
                global selected_keyid
                selected_keyid = keyid
                top.open_box(urwid.Filler(urwid.Pile([
                    urwid.Text('Key %s selected' % keyid),
                    menu_button('OK', close_box, user_args=[2])])))
            items.append(menu_button(keyname(pk), partial(key_chosen, pk['keyid'])))
    items.append(sub_menu(('special', "Create new key"),
        crypto_options()))
    contents = menu(caption, items)
    def open_menu(button):
        return top.open_box(contents)
    return menu_button([caption, u'...'], open_menu)

menu_top = menu('Zeitgitter server configuration', [
    gpg_menu('Choose Signing Key'),
    sub_menu(u'System', [
        sub_menu(u'Preferences', [
            menu_button(u'Appearance', item_chosen),
        ]),
        menu_button(u'Lock Screen', item_chosen),
    ]),
])

class CascadingBoxes(urwid.WidgetPlaceholder):
    max_box_levels = 4

    def __init__(self, box):
        super(CascadingBoxes, self).__init__(urwid.SolidFill('\N{MEDIUM SHADE}'))
        self.box_level = 0
        self.open_box(box)

    def open_box(self, box):
        self.original_widget = urwid.Overlay(urwid.LineBox(box),
            self.original_widget,
            align='center', width=('relative', 80),
            valign='middle', height=('relative', 80),
            min_width=24, min_height=8,
            left=self.box_level * 3,
            right=(self.max_box_levels - self.box_level - 1) * 3,
            top=self.box_level * 2,
            bottom=(self.max_box_levels - self.box_level - 1) * 2)
        self.box_level += 1

    def close_box(self):
        if self.box_level > 1:
            self.original_widget = self.original_widget[0]
            self.box_level -= 1
        else:
            raise urwid.ExitMainLoop

    def keypress(self, size, key):
        if key == 'esc':
            self.close_box()
        elif key == 'tab':
            return super(CascadingBoxes, self).keypress(size, 'down')
        elif key == 'shift tab':
            return super(CascadingBoxes, self).keypress(size, 'up')
        else:
            return super(CascadingBoxes, self).keypress(size, key)


top = CascadingBoxes(menu_top)
palette = [
        ('title', 'dark blue,bold', ''),
        ('special', 'dark blue', ''),
        ('err', 'dark red', ''),
        ('ok', 'dark green', ''),
        ('selected', 'dark blue,standout', ''),
        ('comment', 'dark gray', 'light gray'),
        ('bg', 'light blue', ''),
    ]
urwid.MainLoop(top, palette=palette).run()
print(selected_keyid)
