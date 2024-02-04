#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Goal of this module: Merge multiple acquisitions files into one file.

Two modes are supported: (They cannot be used at the same time)
	- Append time-wise:
		- The order of concatennation is determined by the order of the acquisitions
		  files provided as argument.
		- Start time are interpreted as time lapse between two acquisitions
			- If it is not provided, a null time lapse is assumed.
	- Fusion time wise:
		- The order of the acquisitions files provided as argument is irrevalent.
		- The start time are interpreted in absolute. If they are not provided, it is
		  assumed to start at 0 seconds.
		- Currently, acquisitions with variable time step are not supported. A basic
		  attempt is made to warn the user that the files provided are not supported.


merge -acq file1[;start1] [file2;[start2]]
TODO:
	Core:
		- Implement and test the append mode
		- Implement and test the fuse mode
		- Make the two mode work together?
	Feature:
		- Support nice time format
"""


#########################################################################################
# Modules
#########################################################################################
# Basic python module
import argparse
import sys
from typing import Union, List
from argparse import Namespace

# This project module
import prd


#########################################################################################
# Function
#########################################################################################
def parseAcqArguments(_args: Namespace):
    if _args.headerProvider is not None:
        sys.exit("The option --headProvider is currently not supported.")

    if _args.fuse is None and _args.app is None:
        sys.exit("The script requires the use of one of the two modes (fuse vs app).")

    if _args.fuse is not None and _args.app is not None:
        sys.exit(
            "The script currently only work with one of the two modes (fuse vs "
            "app) activated."
        )

    mergeInfos = []
    if _args.fuse is not None:
        mergeInfos = _args.fuse
        if len(_args.fuse) < 2:
            sys.exit("At least two files are required for the fuse feature.")

    if _args.app is not None:
        mergeInfos = _args.app
        if len(_args.fuse) < 2:
            sys.exit("At least two files are required for the fuse feature.")

    acqPaths, startTime = extractMergeInfo(mergeInfos)

    # TODO: sanity check existance prior starting

    return acqPaths, startTime


def extractMergeInfo(_mergeInfos: List[str]):
    acqPaths = []
    startTime = []

    for cFile in _mergeInfos:
        if cFile.find(";") == -1:
            cAcqPath = cFile
            cStartTime = 0
        else:
            cAcqPath, cStartTime = cFile.split(";")
            # Since we currently assume user always provide in seconds and that the
            # acquisitions files are in milli-seconds.
            cStartTime = float(cStartTime) * 1000.0
        acqPaths.append(cAcqPath)
        startTime.append(cStartTime)

    return acqPaths, startTime


def defineWriter(oFile: Union[str, None], verbose: int):
    if oFile is None:
        if verbose > 0:
            print(
                "Warning: if the output is redirected into a file, the verbosity "
                "might break the file produced."
            )
            input("Press Enter to continue...")
        return sys.stdout.buffer
    else:
        return oFile


#########################################################################################
# Scripting functionnality
#########################################################################################
def parserCreator():
    parser = argparse.ArgumentParser(
        description="Merge multiple acquisitions files " "in a single file. "
    )

    ##################################################
    # Basic
    parser.add_argument(
        "--fuse",
        action="store",
        type=str,
        required=False,
        dest="fuse",
        nargs="+",
        default=None,
        help="File dsa file1[,start1] [file2,[start2]] in s dsa.",
    )
    parser.add_argument(
        "--app",
        action="store",
        type=str,
        required=False,
        dest="app",
        nargs="+",
        default=None,
        help="File dsa file1[,start1] [file2,[start2]] in s dsa.",
    )
    parser.add_argument(
        "--outputFile",
        action="store",
        type=str,
        default=None,
        dest="oFile",
        help="The method used for retention of events.",
    )

    ##################################################
    # Feature
    parser.add_argument(
        "-v",
        "--verbose",
        action="store",
        type=int,
        default=0,
        dest="verbose",
        help="Level of verbosity.",
    )
    parser.add_argument(
        "--headerProvider",
        action="store",
        type=str,
        default=None,
        dest="headerProvider",
        help="Specify which acquisition file will defines the header. If it "
        "is not defined, the header of the first file provided will be "
        " used.",
    )

    return parser.parse_args()


#########################################################################################
# Test functions
#########################################################################################
# n/a


#########################################################################################
# main
#########################################################################################
if __name__ == "__main__":
    args = parserCreator()

    iFiles, startTime = parseAcqArguments(args)

    writerOutput = defineWriter(args.oFile, args.verbose)

    fileIO = []
    allTimeInterval = []
    for cF in iFiles:
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
    sys.exit("Refactoring in process")

    with prd.BinaryPrdExperimentWriter(writerOutput) as writer:
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
                oCurrTB = prd.TimeBlock(
                    id=int(oCurrTime), prompt_events=oPrompt, delayed_events=oDelay
                )
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
