#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''
Goal of this module: Enable the generation of a noisier instance of an acquisition by
eitheir dropping times block or event.


TODO:
	Core:
		- Singles rates is not ajusted.
		- Dead times measurement is not dealt with.
	Feature:
		- Quicker algo
'''

#########################################################################################
# Modules
#########################################################################################
import argparse
import prd
import random
import sys


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
	parser.add_argument('-r', '--retentionFrac', action='store', type=float,
	                    required=True, dest='retFrac',
	                    help='The (expected) fraction of retend events.')
	parser.add_argument('--randoMethod', action='store', choices=["event", "timeBlock"],
	                    default="timeBlock", dest='randoMethod',
	                    help='The method used for retention of events.')
	parser.add_argument('--outputFile', action='store', type=str,
	                    default=None, dest='oFile',
	                    help='The method used for retention of events.')

	##################################################
	# Feature
	parser.add_argument('-s', '--seed', action='store', type=int,
	                    default=None, dest='seed',
	                    help='Defines the seed used for retention method.')
	parser.add_argument('-v', '--verbose', action='store', type=int,
	                    default=0, dest='verbose',
	                    help='Level of verbosity.')

	return parser.parse_args()



#########################################################################################
# Test functions
#########################################################################################
# n/a


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

		# Verbose tracking
		nbTimeBlock = 0
		nbTimeBlockKept = 0
		nbPromptKept = 0
		nbPrompt = 0
		nbDelayKept = 0
		nbDelay = 0
		for tbID, time_block in enumerate(reader.read_time_blocks()):
			nbTimeBlock += 1
			if args.randoMethod == "timeBlock":
				if random.random() < args.retFrac:
					nbTimeBlockKept += 1
					print(f"Current time block {tbID}")
					writer.write_time_blocks((time_block,))
			elif args.randoMethod == "event":
				keptPrompt = []
				for cPr in time_block.prompt_events:
					nbPrompt += 1
					if random.random() < args.retFrac:
						nbPromptKept += 1
						keptPrompt.append(cPr)
				keptDelay = []
				for cDl in time_block.prompt_events:
					nbDelay += 1
					if random.random() < args.retFrac:
						nbDelayKept += 1
						keptDelay.append(cDl)

				tmp = (prd.TimeBlock(id=time_block.id, prompt_events=keptPrompt,
				                     delayed_events=keptDelay),)
				writer.write_time_blocks(tmp)

		if args.verbose > 0 and args.randoMethod == "timeBlock":
			print(f"Number of time block kept {nbTimeBlockKept} out of {nbTimeBlock}. " +
			      f"In percent: {(nbTimeBlockKept / nbTimeBlock) * 100.0}%")

		if args.verbose > 0 and args.randoMethod == "event":
			print(f"Number of prompt kept {nbPromptKept} out of {nbPrompt}. " +
			      f"In percent: {(nbPromptKept / nbPrompt) * 100.0}%")
			print(f"Number of delays kept {nbDelayKept} out of {nbDelay}. " +
			      f"In percent: {(nbDelayKept / nbDelay) * 100.0}%")

		if (nbTimeBlockKept == 0) and (nbPromptKept == 0):
			print("Warning: No prompt or time block were preserved")
			tmp = (prd.TimeBlock(id=0, prompt_events=[]), )
			writer.write_time_blocks(tmp)
