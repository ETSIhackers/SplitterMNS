#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''
Goal of this module: dsa

	Drop ms percent
	Drop per element

TODO:
	Core:
		- Singles rates is not ajusted
	Feature:
		- Quicker algo
'''

#########################################################################################
# Modules
#########################################################################################
import sys
import argparse
import prd


#########################################################################################
# Function
#########################################################################################
def parserCreator():
	parser = argparse.ArgumentParser(description="Create a dsa")

	##################################################
	# Basic
	parser.add_argument('-acqFile', action='store', type=str, required=True,
	                    dest='acq',
	                    help='File dsa .')
	parser.add_argument('-retentionFrac', action='store', type=float, required=True,
	                    dest='ratioDrop',
	                    help='The (expected) fraction of retend events.')
	parser.add_argument('-randoMethod', action='store', choices=["event", "timeBlock"],
	                    default="timeBlock", dest='randoMethod',
	                    help='The method used for retention of events.')
	parser.add_argument('-outputFile', action='store', type=str,
					default=None, dest='oFile',
					help='The method used for retention of events.')

	##################################################
	# Basic

	return parser.parse_args()


#########################################################################################
# main
#########################################################################################
if __name__ == "__main__":
	# do stuff
	args = parserCreator()
