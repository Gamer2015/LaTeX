#!/usr/bin/python
# use python 2 or python 3

import os, sys

def folderSubtract( folder, subtrahend ):
	'''Move all files in subdirs to here, then delete subdirs.
	   Conflicting files are renamed, with 1 appended to their name.'''
	if folder == None or subtrahend == None:
		return

	# remove "/" at the end of the folders
	if folder[-1:-1] == '/':
		folder = folder[0:-1]
	if subtrahend[-1:-1] == '/':
		subtrahend = subtrahend[0:-1]

	for root, dirs, files in os.walk( subtrahend, topdown=False ):
		for name in files:
			source = os.path.join( root, name )
			rel = source[len(subtrahend)+1:]
			folderEquivalent = os.path.join(folder, rel)
			if os.path.exists( folderEquivalent ):
				os.remove(folderEquivalent)

if __name__=='__main__':
	here = os.path.abspath( os.path.dirname( sys.argv[0] ) )
	folderSubtract( sys.argv[1], sys.argv[2] )
