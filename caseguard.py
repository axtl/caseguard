# Copyright (C) 2010 - Alexandru Totolici.  All rights reserved.
# http://hackd.net/wares/caseguard/
#
# This is a small extension for Mercurial (http://www.selenic.com/mercurial)
# that prevents the addition of files to repositories when such additions
# will cause case-folding collisions on certain filesystems. For more
# information, please refer to http://mercurial.selenic.com/wiki/CaseFolding
#
# To enable the "caseguard" extension globally, put these lines in your
# ~/.hgrc:
#  [extensions]
#  caseguard = /path/to/caseguard.py
#
# You may optionally add a section in the config file that specifies what
# options you want to have always enabled:
#
# [caseguard]
# override = true
#
# Please note that having override always enabled will revert the add command
# to its normal behaviour, and caseguard will not block you from adding the
# files to the repository. However, if you pass --verbose you will get a
# listing of the files that will cause problems.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

'''guard against case-folding collisions'''

import re
from mercurial.i18n import _
from mercurial import commands, extensions, cmdutil

addwarning = _('not adding anything: case-collision danger\n')
rmvwarning = _('not removing: case of specified file differs from tracked\n')
adrwarning = _('not allowing addremove: case-collision danger\n')


def casecollide(ui, repo, *pats, **opts):
    '''check the case of the given file against the repository. Return True
    on collisions and (optionally) print a list of problem-files.'''
    colliding = False
    ctx = repo.changectx('tip')
    ctxmanits = [item[0] for item in ctx.manifest().items()]
    pending = ' '.join(repo.status()[2])
    m = cmdutil.match(repo, pats, opts)

    for f in repo.walk(m):
        exact = m.exact(f)
        if exact or f not in repo.dirstate:
            fpat = re.compile(f, re.IGNORECASE)
            for ctxmanit in ctxmanits:
                if fpat.match(ctxmanit):
                    if not fpat.search(pending):
                        colliding = True
                        ui.note(_('%s may cause a case-collision with %s '
                                     '(already in repository)\n' % (f,
                                     ctxmanit)))

    return colliding


def casematch(ui, repo, *pats, **opts):
    '''check if files requested for removal match in case with those on
    disk'''
    matching = True
    ctx = repo.changectx('tip')
    ctxmanits = [item[0] for item in ctx.manifest().items()]
    m = cmdutil.match(repo, pats, opts)
    dirfiles = ' '.join(m.files())

    for ctxmanit in ctxmanits:
        regexmatch = re.search(ctxmanit, dirfiles, re.IGNORECASE)
        if(regexmatch):
            if not re.search(ctxmanit, regexmatch.group(0)):
                matching = False
                ui.note(_('%s not removed, file in repository (%s) has '
                     'different case\n' % (regexmatch.group(0), ctxmanit)))

    return matching


def uisetup(ui):

    def reallyadd(orig, ui, repo, *pats, **opts):
        '''wrap the add command so it enforces that filenames differ in
         more than just case'''
        override = opts['override'] or ui.configbool('caseguard', 'override')
        collision = casecollide(ui, repo, *pats, **opts)
        if not override and collision:
            ui.warn(addwarning)
        else:
            return orig(ui, repo, *pats, **opts)

    def reallyrm(orig, ui, repo, *pats, **opts):
        override = opts['override'] or ui.configbool('caseguard', 'override')
        match = casematch(ui, repo, *pats, **opts)
        if not (override or match):
            ui.warn(rmvwarning)
        else:
            return orig(ui, repo, *pats, **opts)

    def reallyaddremove(orig, ui, repo, *pats, **opts):
        override = opts['override'] or ui.configbool('caseguard', 'override')
        collision = casecollide(ui, repo, *pats, **opts)
        if not override and collision:
            ui.warn(adrwarning)
        else:
            return orig(ui, repo, *pats, **opts)

    wrapadd = extensions.wrapcommand(commands.table, 'add', reallyadd)
    wrapadd[1].append(('o', 'override', False, _('add files regardless of '
    'possible case-collision problems')))

    wraprm = extensions.wrapcommand(commands.table, 'rm', reallyrm)
    wraprm[1].append(('o', 'override', False, _('remove files regardless of '
    'differences in case')))

    wrapaddremove = extensions.wrapcommand(commands.table, 'addremove',
    reallyaddremove)
    wrapaddremove[1].append(('o', 'override', False, _('add/remove files '
    'regardless of differences in case')))
