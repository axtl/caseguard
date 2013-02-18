caseguard
=========

**NOTE**: This extension is no longer needed as of hg >= 1.9, as this
functionality is now built-in.

***

Caseguard protects repositories against name-related problems:

1. _'folding case'_ where filenames with only case differences cause problems
on non-case-preserving systems (Windows, OS X in default configuration)
2. _'non-portable file names'_ that trigger issues, particularly on Windows;
([list](http://bitquabit.com/post/zombie-operating-systems-and-aspnet-mvc/)]

