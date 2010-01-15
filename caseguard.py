
'''guard against case-folding collisions on Mac OS X, by blocking an add that would cause a collision'''

from mercurial.i18n import _
from mercurial import hg, commands

'''figure out either:
    a) how to override the add command
        in this case, we can verify there is no regexp match to any non-removed files.
        figure out of hg knows about a files with a regexp/similar name
            from hg log and friends, although i expect that, given a file, mercurial can pull its path in the repo and then we can use the filename as a base to request logs of regex-matched names
        check the file status:
            removed, in changeset, checked in and repo updated -> no problem
            removed, not checked in -> case-fold, abort and request rename (print out old file name)
            removed, not checked in -> works OK, it respects order of operations
            other states?
        if filesystem (re)move, then new file, then hg rm oldcase, file overwrite, not to worry (unless we want to caseguard the hg rm too, show warning when the user is about to remove an inexact match)
    b) a pre-add hook
        is 'add' (preadd) hookable?
        is a hook enforceable? 
'''