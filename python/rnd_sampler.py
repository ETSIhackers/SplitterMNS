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
		- with thingy
'''

#########################################################################################
# Modules
#########################################################################################
import argparse
import random
import sys
import prd


#########################################################################################
# Function
#########################################################################################
def parserCreator():
	parser = argparse.ArgumentParser(description="Create a dsa")

	##################################################
	# Basic
	parser.add_argument('--acqFile', action='store', type=str, required=True,
	                    dest='acq',
	                    help='File dsa .')
	parser.add_argument('-r', '--retentionFrac', action='store', type=float, required=True,
	                    dest='retFrac',
	                    help='The (expected) fraction of retend events.')
	parser.add_argument('--randoMethod', action='store', choices=["event", "timeBlock"],
	                    default="timeBlock", dest='randoMethod',
	                    help='The method used for retention of events.')
	parser.add_argument('--outputFile', action='store', type=str,
	                    default=None, dest='oFile',
	                    help='The method used for retention of events.')

	##################################################
	# Feature
	parser.add_argument('-seed', action='store', type=int,
					default=None, dest='seed',
					help='Defines the seed used for retention method.')
	parser.add_argument('-verbose', action='store', type=int,
					default=0, dest='verbose',
					help='Level of verbosity.')

	return parser.parse_args()


#########################################################################################
# main
#########################################################################################
if __name__ == "__main__":
	# do stuff
	args = parserCreator()

	if args.seed is not None:
		random.seed(args.seed)

	if args.oFile is None:
		writerIO = sys.stdout.buffer
	else:
		writerIO = args.oFile

	with prd.BinaryPrdExperimentWriter(writerIO) as writer:

		reader = prd.BinaryPrdExperimentReader(args.acq)
		header = reader.read_header()
		writer.write_header(header)

		nbTimeBlock = 0
		nbTimeBlockKept = 0
		nbPrompt = 0
		for tbID, time_block in enumerate(reader.read_time_blocks()):
			nbTimeBlock += 1
			if args.randoMethod == "timeBlock":
				# nbPrompt += len(time_block.prompt_event)
				if random.random() < args.retFrac:
					nbTimeBlockKept += 1
					print(f"Current time block {tbID}")
					tmp = (prd.TimeBlock(id=time_block.id, prompt_events=time_block.prompt_events), )
					writer.write_time_blocks(tmp)
			elif args.randoMethod == "event":
				dsa = 0
				# for event in time_block.prompt_events:
				# 	dsa
		print(f"Number of time block {nbTimeBlock}")

		if nbTimeBlockKept == 0:
			print("Warning: No event/time block were preserved")
			tmp = (prd.TimeBlock(id=0, prompt_events=[]), )
			writer.write_time_blocks(tmp)


# Expected: 16,722,947
# Current:  16,722,946
