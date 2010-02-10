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
from mercurial.i18n import _
from mercurial import commands, extensions, cmdutil

warning = _('abort: case-fold collision danger\n')


def casecollide(ui, repo, *pats, **opts):
    '''check the case of the given file against the repository. Return True
    on collisions and (optionally) print a list of problem-files.'''
    colliding = False
    # normpats = set(map(str.lower, pats))
    #     if len(normpats) != len(pats):
    #         colliding = True
    #         ui.note('file list contains a possible case-fold collision\n')
    #         return colliding
    ctx = repo['.']
    modified, added, removed, deleted, unknown, ignored, clean = repo.status()
    ctxmanits = [item[0] for item in ctx.manifest().items()] + added
    pending = ' '.join(removed)
    m = cmdutil.match(repo, pats, opts)

    for f in repo.walk(m):
        exact = m.exact(f)
        if exact or f not in repo.dirstate:
            fpat = re.compile(f+'\Z', re.IGNORECASE)
            for ctxmanit in ctxmanits:
                if fpat.match(ctxmanit) and not fpat.search(pending):
                    colliding = True
                    ui.note(_('adding %s may cause a case-collision with %s'
                    ' (already managed)\n' % (f, ctxmanit)))
                else:
                    pending = pending + ' ' + f
                    print pending

    return colliding


def casematch(ui, repo, *pats, **opts):
    '''check if files requested for removal match in case with those on
    disk'''
    matching = True
    ctx = repo['.']
    ctxmanits = [item[0] for item in ctx.manifest().items()]
    m = cmdutil.match(repo, pats, opts)
    dirfiles = ' '.join(m.files())

    for ctxmanit in ctxmanits:
        regexmatch = re.search(ctxmanit, dirfiles, re.IGNORECASE)
        if(regexmatch) and not re.search(ctxmanit, regexmatch.group(0)):
            matching = False
            ui.note(_('removing %s may cause data-loss: the file in the'
            ' repository (%s) has different case\n' % (regexmatch.group(0),
            ctxmanit)))

    return matching


def uisetup(ui):

    def reallyadd(orig, ui, repo, *pats, **opts):
        '''wrap the add command so it enforces that filenames differ in
         more than just case'''
        override = opts['override'] or ui.configbool('caseguard', 'override')
        collision = casecollide(ui, repo, *pats, **opts)
        if not override and collision:
            ui.warn(warning)
        else:
            return orig(ui, repo, *pats, **opts)

    def reallyrm(orig, ui, repo, *pats, **opts):
        '''wrap the rm command so it enforces that files to be removed match
         exactly (in case) the ones tracked by the repository'''
        override = opts['override'] or ui.configbool('caseguard', 'override')
        match = casematch(ui, repo, *pats, **opts)
        if not (override or match):
            ui.warn(warning)
        else:
            return orig(ui, repo, *pats, **opts)

    wrapadd = extensions.wrapcommand(commands.table, 'add', reallyadd)
    wrapadd[1].append(('o', 'override', False, _('add files regardless of '
    'possible case-collision problems')))

    wraprm = extensions.wrapcommand(commands.table, 'rm', reallyrm)
    wraprm[1].append(('o', 'override', False, _('remove files regardless of '
    'differences in case')))

    wrapaddremove = extensions.wrapcommand(commands.table, 'addremove',
    reallyadd)
    wrapaddremove[1].append(('o', 'override', False, _('add/remove files '
    'regardless of differences in case')))
