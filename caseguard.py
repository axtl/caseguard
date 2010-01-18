# Copyright (C) 2010 - Alexandru Totolici.  All rights reserved.
# http://hackd.net/wares/caseguard/
#
# This is a small extension for Mercurial (http://www.selenic.com/mercurial)
# that prevents the addition of files to repositories when such additions
# will cause case-folding collisions on certain filesystems.
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
# silent = true
# override = true
#
# Please note that having override always enabled will revert the add command
# to its normal behaviour, and caseguard will not block you from adding the
# files to the repository. However, if silent = false, you will still get a
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

'''Guard against case-folding collisions by blocking the 'add' operation if \
it would cause a collision on the local repository'''

import re
from mercurial.i18n import _
from mercurial import commands, extensions, cmdutil

warning = _("""    Case-collision danger\n""")


def uisetup(ui):

    def reallyadd(orig, ui, repo, override=False, silent=False, \
        *pats, **opts):
        override |= ui.configbool('caseguard', 'override')
        silent |= ui.configbool('caseguard', 'silent')
        collision = casecollide(repo, silent, *pats, **opts)
        if not override and collision:
            ui.warn(warning)
        else:
            return orig(ui, repo, *pats, **opts)

    entry = extensions.wrapcommand(commands.table, 'add', reallyadd)
    entry[1].append(('o', 'override', False, _('add files regardless of \
possible case-collision problems')))
    entry[1].append(('s', 'silent', False, _('do not output a list of \
case-colliding files')))

    '''Check the case of the given file against the repository. Return \
True on collisions and print a list of problem-files'''

    def casecollide(repo, silent, *pats, **opts):
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
                            if not silent:
                                ui.status(_('EEE> %s and %s (tracked): \
case-collision danger\n' % (f, ctxmanit)))
                            else:
                                return colliding

        return colliding
