# This Mercurial extension prevents users from adding both FOO and foo to a
# repository, or Windows-reserved filenames. Certain filesystems cannot handle
# cases where files differ only by case (i.e. foo and FOO) and Mercurial would
# report a case-folding collision if a user tried to update to a revision
# containing such a state. For more information, please see:
# http://mercurial.selenic.com/wiki/CaseFolding
#
# The operations that caseguard currently handles are 'add' and 'addremove'.
#
# Renaming file1 to FILE1 and running addremove will NOT change what the
# repository tracks. All changes must be committed before caseguard will
# allow files to be added (this means 'hg rm foo; hg add FOO' will fail).
#
# To enable the "caseguard" extension globally, put these lines in your
# ~/.hgrc:
#  [extensions]
#  caseguard = /path/to/caseguard.py
#
# You may optionally add a section in the config file that specifies what
# options you want to have always enabled:
#
#   [caseguard]
#   override = true
#   nowincheck = true
#
# You cannot enable -U/--unguard in the config file since this effectively
# disables the extension.
#
# Please note that having override always enabled will revert all commands
# to their normal behaviour. However, if you pass --verbose you will get a
# listing of the files that would cause problems.
#
# Copyright (C) 2010 - Alexandru Totolici
# http://hackd.net/projects/caseguard/
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

'''guard against case-fold collisions and Windows name incompatibilities'''

import re
from mercurial import commands, extensions, cmdutil
from mercurial.i18n import _


casewarn = _('case-collision danger\n')
namewarn = _('Windows-incompatible filenames detected\n')


def casecollide(ui, repo, *pats, **opts):
    '''check the case of the given file against the repository. Return True
    on collisions and (optionally) print a list of problem-files.'''
    reserved = False
    colliding = False
    casefold = False

    override = opts['override'] or ui.configbool('caseguard', 'override')
    nowinchk = opts['nowincheck'] or ui.configbool('caseguard', 'nowincheck')
    winbanpat = re.compile('((com[1-9](\..*)?)|(lpt[1-9](\..*)?)|'
        '(con(\..*)?)|(aux(\..*)?)|(prn(\..*)?)|(nul(\..*)?)|(CLOCK\$))\Z',
        re.IGNORECASE)
    badchars = re.compile('(^ )|\\\|\?|\%|\*|\:|\||\"|\<|\>|((\.|\ )$)')

    if len(set(s.lower() for s in pats)) != len(pats):
        colliding = True
        ui.note(_('file list contains a possible case-fold collision\n'))

    added = repo.status()[1]
    exclst = [item[0] for item in repo['.'].manifest().items()] + added
    chklst = [item.lower() for item in exclst]
    mtch = dict(zip(chklst, exclst))
    m = cmdutil.match(repo, pats, opts)

    for f in repo.walk(m):
        flwr = f.lower()
        if winbanpat.match(f):
            reserved = True
            ui.note(_('%s is a reserved name on Windows\n') % f)
        if badchars.search(f):
            reserved = True
            ui.note(_('%s contains Windows-illegal characters\n') % f)
        if f not in repo.dirstate and f not in exclst and flwr in mtch:
            colliding = True
            ui.note(_('adding %s may cause a case-fold collision with %s\n') %
                (f, mtch[flwr]))

        mtch[flwr] = f

    casefold = not override and ((reserved and not nowinchk) or colliding)

    return casefold, colliding, reserved and not nowinchk


def uisetup(ui):

    def reallyadd(orig, ui, repo, *pats, **opts):
        '''wrap the add command so it enforces that filenames differ in
        more than just case
        '''
        if opts['unguard']:
            return orig(ui, repo, *pats, **opts)
        casefold, collision, reserved = casecollide(ui, repo, *pats, **opts)
        if casefold:
            if reserved and collision:
                ui.warn(_("abort:\n"))
                ui.warn("   " + namewarn)
                ui.warn("   " + casewarn)
            elif reserved:
                ui.warn(_("abort: ") + namewarn)
            elif collision:
                ui.warn(_("abort: ") + casewarn)
            return 255
        else:
            return orig(ui, repo, *pats, **opts)

    wraplist = [extensions.wrapcommand(commands.table, 'add', reallyadd),
        extensions.wrapcommand(commands.table, 'addremove', reallyadd)]

    for wrapcmd in wraplist:
        wrapcmd[1].append(('o', 'override', False, _('add files regardless of'
        ' possible case-collision problems')))
        wrapcmd[1].append(('w', 'nowincheck', False, _('do not check'
        ' filenames for Windows incompatibilities')))
        wrapcmd[1].append(('U', 'unguard', False, _('completely skip checks'
        ' related to case-collision problems')))
