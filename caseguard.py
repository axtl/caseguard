'''Guard against case-folding collisions by blocking the 'add' operation if it would cause a collision on the local repository'''

import re
from mercurial.i18n import _
from mercurial import commands, extensions, cmdutil

'''
TODO: add opts
TODO: a better error message... maybe.
'''

warning = _("""
    I can't let you do that, Dave.
""")

def uisetup(ui):
    def reallyadd(orig, ui, repo, *pats, **opts):
        if casecollide(repo, *pats, **opts):
            ui.warn(warning)
        else:
            return orig(ui, repo, *pats, **opts)

    entry = extensions.wrapcommand(commands.table, 'add', reallyadd)

    '''Check the case of the given file against the repository. Return True on collisions and print a list of problem-files'''
    def casecollide(repo, *pats, **opts):
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
                            ui.status(_('EEE> %s and %s (tracked): case-collision danger\n' % (f, ctxmanit)))

        return colliding