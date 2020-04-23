#!/usr/bin/python
# use python 2 or python 3

import os, sys

def reduceDuplicateCounterByAtMost1( here ):
    '''Move all files in subdirs to here, then delete subdirs.
       Conflicting files are renamed, with 1 appended to their name.'''
    for root, dirs, files in os.walk( here, topdown=False ):
        files.sort()
        for name in files:
            source = os.path.join( root, name )
            
            base, ext = os.path.splitext( source )
            start = base.rfind("(")
            end = base.rfind(")")
            if(start == -1 or end == -1):
                continue
            
            number = base[start+1: end]
            if number.isnumeric() and end == len(base) - 1:
                base = base[0:-3]
                number = int(number)-1
                if number > 0:
                    base += "("+str(number)+")" 
            
            target = base + ext
            if os.path.exists( target ) == False:
                os.rename( source, target )


if __name__=='__main__':
    here = os.path.abspath( os.path.dirname( sys.argv[0] ) )
    reduceDuplicateCounterByAtMost1( here )
