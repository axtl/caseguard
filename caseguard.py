# This is a small extension for Mercurial (http://www.selenic.com/mercurial)
# that prevents certain mercurial commands from executing, by enforcing all
# operations to be case-sensitive, regardless of the filesystem. For more
# information on case-folding collisions, please refer to
# http://mercurial.selenic.com/wiki/CaseFolding
#
# The operations that caseguard currently handles are:
#
#   - add:
#               files to be added must be different than any tracked files in
#               more than just case
#   - rm:
#               files to be removed must match exactly to those that are
#               tracked
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

casewarn = _('abort: case-collision danger\n')
namewarn = _('abort: Windows-reserved filenames detected\n')


def casecollide(ui, repo, *pats, **opts):
    '''check the case of the given file against the repository. Return True
    on collisions and (optionally) print a list of problem-files.'''
    reserved = False
    colliding = False
    reasons = set()

    override = opts['override'] or ui.configbool('caseguard', 'override')
    winchk = not (opts['nowincheck'] or ui.configbool('caseguard',
        'nowincheck'))
    winbanpat = re.compile('((com[1-9](\..*)?)|(lpt[1-9](\..*)?)|'
        '(con(\..*)?)|(aux(\..*)?)|(prn(\..*)?)|(nul(\..*)?)|(CLOCK\$))\Z',
        re.IGNORECASE)

    normpats = set(s.lower() for s in pats)
    if len(normpats) != len(pats):
        colliding = True
        ui.note('file list contains a possible case-fold collision\n')
        if not override:
            reasons.add(casewarn)
            return colliding, reasons

    ctx = repo['.']
    modified, added, removed, deleted, unknown, ignored, clean = repo.status()
    ctxmanits = [item[0] for item in ctx.manifest().items()] + added
    removing = ' '.join(removed)
    pending = ''
    m = cmdutil.match(repo, pats, opts)

    for f in repo.walk(m):
        if winbanpat.match(f):
            reserved = True
            if winchk:
                reasons.add(namewarn)
            ui.note(_('%s is a reserved name on Windows\n') % f)
        exact = m.exact(f)
        if exact or f not in repo.dirstate:
            fpat = re.compile(f+'\Z', re.IGNORECASE)
            for ctxmanit in ctxmanits:
                if fpat.match(ctxmanit) or fpat.search(pending) and not \
                    fpat.search(removing):
                    colliding = True
                    if not override:
                        reasons.add(casewarn)
                    ui.note(_('adding %s may cause a case-fold collision with'
                        ' %s (already managed)\n' % (f, ctxmanit)))
            else:
                pending += f + ' '

    colliding = (reserved and winchk) or (colliding and not override)

    return colliding, reasons


def uisetup(ui):

    def reallyadd(orig, ui, repo, *pats, **opts):
        '''wrap the add command so it enforces that filenames differ in
        more than just case
        '''
        collision, reasons = casecollide(ui, repo, *pats, **opts)
        if collision:
            for reason in reasons:
                ui.warn(reason)
        else:
            return orig(ui, repo, *pats, **opts)

    wraplist = [extensions.wrapcommand(commands.table, 'add', reallyadd),
    extensions.wrapcommand(commands.table, 'addremove', reallyadd)]

    for wrapcmd in wraplist:
        wrapcmd[1].append(('o', 'override', False, _('add files regardless of'
        ' possible case-collision problems')))
        wrapcmd[1].append(('w', 'nowincheck', False, _('do not check'
        ' filenames for Windows-reserved names')))
