'''Guard against case-folding collisions on Mac OS X, by blocking an add that would cause a collision'''

import platform
import re
from mercurial.i18n import _
from mercurial import commands, extensions

'''
TODO: a better error message... maybe.

'''

warning = _("""
    I can't let you do that, Dave. 
    
""")

def uisetup(ui):
    if oscheck()==False:
        ''' default return, this is not the extension they are looking for (non-Darwin) '''
        return 
    def reallyadd(orig, ui, repo, *pats, **opts):
        if  casecollide(repo):
            ui.warn(warning)
        else:
            return orig(ui, repo, *pats, **opts)

    entry = extensions.wrapcommand(commands.table, 'add', reallyadd)

'''Check the case of the given file against the repository. Return True on collisions'''
''' TODO: fill in'''
''' TODO: proper argument list'''
def casecollide(repo):
    return False
    
''' Check to make sure that we are running on OS X'''
def oscheck():
    osname = platform.system()
    return re.match('[dD]arwin', osname)