#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Goal of this module: Merge multiple acquisitions files into one file.

Two modes are supported: (They cannot be used at the same time right now)
	- Append time-wise: (Not supported presently)
		- The order of concatennation is determined by the order of the acquisitions
		  files provided as argument.
		- Start time are interpreted as time lapse between two acquisitions
			- If it is not provided, a null time lapse is assumed.
	- Fusion time wise:
		- The order of the acquisitions files provided as argument is irrevalent.
		- The start time are interpreted in absolute. If they are not provided, it is
		  assumed to start at 0 ms.

Limitations:
    - Acquisitions with variable time step are not supported.
    - It is assumed that the smallest time interval possible is 1 ms.

Assumptions:
    - Empty time block do not need to be defined

merge -acq file1[,start1] [file2,[start2]]
TODO:
	Core:
		- Clean (qwe) and test the fuse mode
		- Implement and test the append mode
		- Make the two mode work together?
	Feature:
		- Support nice time format
"""


#########################################################################################
# Modules
#########################################################################################
# Basic python module
import argparse
from argparse import Namespace
import random
import sys
from typing import Union, List

# This project module
import prd


#########################################################################################
# Function
#########################################################################################
def parseAcqArguments(_args: Namespace):
    if _args.merge is None and _args.app is None:
        sys.exit("The script requires the use of one of the two modes (merge vs app).")

    if _args.merge is not None and _args.app is not None:
        sys.exit(
            "The script currently only work with one of the two modes (merge vs "
            "app) activated."
        )

    mergeInfos = []
    if _args.merge is not None:
        mergeInfos = _args.merge
        if len(_args.merge) < 2:
            sys.exit("At least two files are required for the fuse feature.")

    if _args.app is not None:
        mergeInfos = _args.app
        if len(_args.merge) < 2:
            sys.exit("At least two files are required for the fuse feature.")

    acqPaths, startTime = extractMergeInfo(mergeInfos)

    # TODO: sanity check existance of input/output files prior starting

    return acqPaths, startTime


def extractMergeInfo(_mergeInfos: List[str]):
    acqPaths = []
    startTime = []

    for cFile in _mergeInfos:
        if cFile.find(",") == -1:
            cAcqPath = cFile
            cStartTime = 0
        else:
            cAcqPath, cStartTime = cFile.split(",")
            # Since we currently assume user always provide in seconds and that the
            # acquisitions files are in milli-seconds.
            # assuming smallest is ms
            cStartTime = int(float(cStartTime) * 1000)
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
        description="Merge multiple acquisitions files in a single file. The argument format for append/merge is file1[,start1] [file2,[start2]] [file3,[start3]]"
    )

    ##################################################
    # Basic
    parser.add_argument(
        "--merge",
        action="store",
        type=str,
        required=False,
        dest="merge",
        nargs="+",
        default=None,
        help="Acquisition files to merge. Start time are in seconds and they are interpreted in absolute.",
    )
    parser.add_argument(
        "--app",
        action="store",
        type=str,
        required=False,
        dest="app",
        nargs="+",
        default=None,
        help="Acquisition files to append. Start time and in seconds and they are interpreted in relative to the end time of the last acquisition.",
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
    parser.add_argument(
        "-s",
        "--shuffleEvents",
        action="store_true",
        default=False,
        dest="shuffleEvents",
        help="Shuffle the events in time block that are merged.",
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

    if args.app is not None:
        sys.exit("Append mode is not implemented yet")

    iFiles, startTime = parseAcqArguments(args)

    writerOutput = defineWriter(args.oFile, args.verbose)

    # qwe create a method for preparation
    fileIO = []
    allTimeInterval = []
    for i, cF in enumerate(iFiles):
        cFileIO = prd.BinaryPrdExperimentReader(cF)
        header = cFileIO.read_header()
        if (i == 0) and (args.headerProvider == None):
            oHeader = header
        allTimeInterval.append(header.scanner.listmode_time_block_duration)
        fileIO.append(cFileIO.read_time_blocks())
    if len(set(allTimeInterval)) != 1:
        sys.exit(
            f"This script does not support variable time block size. The time block are {allTimeInterval}."
        )
    else:
        # Convert startime from ID of ms to ID of time interval of the files
        startTime = [int(cStartTime * allTimeInterval[0]) for cStartTime in startTime]

    if args.headerProvider is not None:
        oHeader = prd.BinaryPrdExperimentReader(args.headerProvider).read_header()

    # Create a method for the merge case
    # Merge case
    mFileNextTimeBlock = []
    timeBlockBuffer = []
    for i, cFileIO in enumerate(fileIO):
        fTimeBlock = next(cFileIO)
        mFileNextTimeBlock.append(fTimeBlock.id + startTime[i])
        timeBlockBuffer.append(fTimeBlock)

    cTime = min(mFileNextTimeBlock)
    with prd.BinaryPrdExperimentWriter(writerOutput) as writer:
        writer.write_header(oHeader)

        while True:
            cPrompts = []
            cDelays = []
            nbMerged = 0
            removeFile = []
            for i in range(len(mFileNextTimeBlock)):
                if mFileNextTimeBlock[i] <= cTime:
                    cTimeBlock = timeBlockBuffer[i]
                    cPrompts.extend(cTimeBlock.prompt_events)
                    if cTimeBlock.delayed_events is not None:
                        cDelays.extend(cTimeBlock.delayed_events)
                    nbMerged += 1
                    # Update info
                    try:
                        timeBlockBuffer[i] = next(fileIO[i])
                        mFileNextTimeBlock[i] = timeBlockBuffer[i].id + startTime[i]
                    except StopIteration:
                        removeFile.append(i)
            if nbMerged > 1 and args.shuffleEvents:
                random.shuffle(cPrompts)
            if len(cDelays) == 0:
                cDelays = None
            else:
                if nbMerged > 1 and args.shuffleEvents:
                    random.shuffle(cPrompts)

            mTimeBlock = (
                prd.TimeBlock(id=cTime, prompt_events=cPrompts, delayed_events=cDelays),
            )
            writer.write_time_blocks(mTimeBlock)

            if len(removeFile) != 0:
                # Pop in reverse order to not break anything
                for cPos in removeFile[::-1]:
                    fileIO.pop(cPos)
                    mFileNextTimeBlock.pop(cPos)
                    timeBlockBuffer.pop(cPos)
                    startTime.pop(cPos)
            if len(fileIO) == 0:
                break
            else:
                cTime = min(mFileNextTimeBlock)
