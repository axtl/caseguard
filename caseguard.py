# This Mercurial extension prevents users from adding both FOO and foo to a
# repository, or Windows-reserved filenames. Certain filesystems cannot handle
# cases where files differ only by case (i.e. foo and FOO) and Mercurial would
# report a case-folding collision if a user tried to update to a revision
# containing such a state. For more information, see:
# http://mercurial.selenic.com/wiki/CaseFolding
#
# The operations that caseguard currently handles are:
#
#   - add:
#               files to be added must be different than any tracked files in
#               more than just case
#   - addremove:
#               currently, same behaviour as add
#
# Please note that renaming file1 to FILE1 and running addremove will NOT
# change what the repository tracks. This is planned for a future release.
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
# Please note that having override always enabled will revert all commands
# to their normal behaviour. However, if you pass --verbose you will get a
# listing of the files that would cause problems.
#
# Copyright (C) 2010 - Alexandru Totolici
# http://hackd.net/projects/caseguard/
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

'''guard against case-fold collisions'''

import re
from mercurial import commands, extensions, cmdutil
from mercurial.i18n import _


casewarn = _('case-collision danger\n')
namewarn = _('Windows-reserved filenames detected\n')


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

    normpats = set(s.lower() for s in pats)
    if len(normpats) != len(pats):
        colliding = True
        ui.note(_('file list contains a possible case-fold collision\n'))

    ctx = repo['.']
    modified, added, removed, deleted, unknown, ignored, clean = repo.status()
    exclst = [item[0] for item in ctx.manifest().items()] + added
    chklst = [item.lower() for item in exclst]
    mtch = dict(zip(chklst, exclst))
    m = cmdutil.match(repo, pats, opts)
    walker = repo.walk(m)

    for f in walker:
        if winbanpat.match(f):
            reserved = True
            ui.note(_('%s is a reserved name on Windows\n') % f)
        if f not in repo.dirstate and f.lower() in mtch and f not in exclst:
            colliding = True
            ui.note(_('adding %s may cause a case-fold collision with %s\n') %
                (f, mtch[f.lower()]))

        mtch[f.lower()] = f

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
        ' filenames for Windows-reserved names')))
        wrapcmd[1].append(('U', 'unguard', False, _('completely skip checks'
        ' related to case-collision problems')))
