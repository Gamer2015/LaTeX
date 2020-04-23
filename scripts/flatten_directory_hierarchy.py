#!/usr/bin/python
# use python 2 or python 3

import os, sys

def flattenFiles( here ):
	'''Move all files in subdirs to here, then delete subdirs.
	   Conflicting files are renamed, with 1 appended to their name.'''
	for root, dirs, files in os.walk( here, topdown=False ):
		if root != here:
			for name in files:
				source = os.path.join( root, name )
				target = handleDuplicates( os.path.join( here, name ) )
				os.rename( source, target )

		for name in dirs:
			os.rmdir( os.path.join( root, name ) )

def handleDuplicates( target ):
	base, ext = os.path.splitext( target )	
	duplicates = 0
	while os.path.exists( target ):
		duplicates += 1
		target    = base + '(' + str(duplicates) + ')' + ext
	return target


if __name__=='__main__':
	here = os.path.abspath( os.path.dirname( sys.argv[0] ) )
	flattenFiles( here )
