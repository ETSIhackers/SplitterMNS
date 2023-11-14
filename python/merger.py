#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''
Goal of this module: dsa
merge -acq file1[;start1] [file2;[start2]]


dsa currently merge on the left and in the largest

TODO:
	Core:
		- dsa
	Feature:
		- Support nice time format
'''


#########################################################################################
# Modules
#########################################################################################
import argparse
import copy
# from datetime import datetime
import prd
import sys


#########################################################################################
# Function
#########################################################################################
def parserCreator():
	parser = argparse.ArgumentParser(description="Create a dsa")

	##################################################
	# Basic
	parser.add_argument('--acqFile', action='store', type=str, required=True,
	                    dest='acq', nargs='+',
	                    help='File dsa file1[,start1] [file2,[start2]] in s dsa.')
	parser.add_argument('--outputFile', action='store', type=str,
	                    default=None, dest='oFile',
	                    help='The method used for retention of events.')
	parser.add_argument('--app', action='store_true',
	                    default=False, dest='app',
	                    help='dsa .')

	##################################################
	# Feature
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

	if args.oFile is None:
		writerIO = sys.stdout.buffer
	else:
		writerIO = args.oFile

	# fileName = [file.split(",")[0] for file in args.acq]
	fileName = []
	startTime = []
	for cFile in args.acq:
		tmp = cFile.split(",")
		fileName.append(tmp[0])
		if len(tmp) > 2:
			sys.exit("The number of information provided per file should be two at maximum. It is divided per commas")
		elif len(tmp) == 2:
			startTime.append(float(tmp[1]) * 1000)
			print(startTime)
		else:
			startTime.append(0)

	fileIO = []
	allTimeInterval = []
	for cF in fileName:
		cFileIO = prd.BinaryPrdExperimentReader(cF)
		header = cFileIO.read_header()
		allTimeInterval.append(header.scanner.listmode_time_block_duration)
		fileIO.append(cFileIO.read_time_blocks())
		#
		# fileIO.append(prd.BinaryPrdExperimentReader(cF))
		# header = fileIO[-1].read_header()
		# allTimeInterval.append(header.scanner.listmode_time_block_duration)
		#
		# dsa take care about diff header

	with prd.BinaryPrdExperimentWriter(writerIO) as writer:
		writer.write_header(header)
		oTimeInterval = max(allTimeInterval)

		oCurrTime = 0

		future = oCurrTime + oTimeInterval
		filesBuffer = []

		while True:
			for i, cFIO in enumerate(fileIO):
				if cFIO is not None:
					# while filesBuffer[i] is None:
					while True:
						try:
							cTB = next(cFIO)
						except StopIteration:
							fileIO[i] = None
							break

						if future > cTB.id * allTimeInterval[i] + startTime[i]:
							filesBuffer.append(cTB)
						else:
							break

			if len(filesBuffer) != 0:
				oPrompt = []
				oDelay = []
				for cTb in filesBuffer:
					oPrompt += cTb.prompt_events
					if cTb.delayed_events is not None:
						oDelay += cTb.delayed_events
				if len(oDelay) == 0:
					oDelay = None
				oCurrTB = prd.TimeBlock(id=int(oCurrTime), prompt_events=oPrompt,
				                     delayed_events=oDelay)
				writer.write_time_blocks((oCurrTB,))
			else:
				break

			oCurrTime += oTimeInterval
			future += oTimeInterval

	# print(fileName)
	# print(startTime)


		# future = oCurrTime + oTimeInterval
		# stillThingToProcesss = True
		# filesBuffer = len(allTimeInterval) * [None,]

		# while stillThingToProcesss:
		# 	for i, cFIO in enumerate(fileIO):
		# 		if filesBuffer[i] is not None:
		# 			if future > filesBuffer[i].id * allTimeInterval[i] + startTime[i]:
		# 				writer.write_time_blocks((filesBuffer[i],))
		# 				filesBuffer[i] = None
		# 			else:
		# 				break
		# 		if cFIO is not None:
		# 			while filesBuffer[i] is None:
		# 				try:
		# 					cTB = next(cFIO)
		# 				except StopIteration:
		# 					fileIO[i] = None
		# 					break

		# 				if future > cTB.id * allTimeInterval[i] + startTime[i]:
		# 					writer.write_time_blocks((cTB,))
		# 				else:
		# 					filesBuffer[i] = copy.deepcopy(cTB)


		# 	future += oTimeInterval
