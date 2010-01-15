'''Guard against case-folding collisions by blocking the 'add' operation if it would cause a collision on the local repository'''

from mercurial.i18n import _
from mercurial import commands, extensions

'''
TODO: a better error message... maybe.

'''

warning = _("""

    I can't let you do that, Dave. 
    
""")

def uisetup(ui):
    def reallyadd(orig, ui, repo, *pats, **opts):
        if casecollide(repo):
            ui.warn(warning)
        else:
            return orig(ui, repo, *pats, **opts)

    entry = extensions.wrapcommand(commands.table, 'add', reallyadd)

'''Check the case of the given file against the repository. Return True on collisions'''
''' TODO: fill in'''
''' TODO: proper argument list'''
def casecollide(repo):
    return False
