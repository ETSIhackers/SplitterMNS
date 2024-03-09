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
from prd.types import CoincidenceEvent


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
    else:
        mergeInfos = _args.app

    if len(mergeInfos) < 2:
        sys.exit("At least two files are required for the merge feature.")

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


def setupFileIO(
    _iFiles: List[str], _startTime: List[int], _headerProvider: Union[str, None]
):
    fileIO = []
    allTimeInterval = []
    for i, cF in enumerate(_iFiles):
        cFileIO = prd.BinaryPrdExperimentReader(cF)
        header = cFileIO.read_header()
        if i == 0:
            firstHeader = header
        allTimeInterval.append(header.scanner.listmode_time_block_duration)
        fileIO.append(cFileIO.read_time_blocks())

    if len(set(allTimeInterval)) != 1:
        sys.exit(
            f"This script does not support variable time block size. The time blocks are {allTimeInterval}."
        )
    # Convert startime from ms to ID of time interval of the files
    startTimeBlockId = [
        int(cStartTime * allTimeInterval[0]) for cStartTime in _startTime
    ]

    if _headerProvider is not None:
        oHeader = prd.BinaryPrdExperimentReader(_headerProvider).read_header()
    else:
        oHeader = firstHeader

    return fileIO, startTimeBlockId, oHeader


def createTimeBlock(
    _cTime: int,
    _cPrompts: List[CoincidenceEvent],
    _cDelays: List[CoincidenceEvent],
    _nbMerged: int,
    _shuffleEvents: bool,
):
    if _nbMerged > 1 and _shuffleEvents:
        random.shuffle(_cPrompts)

    if len(_cDelays) == 0:
        cDelays = None
    else:
        cDelays = _cDelays
        if _nbMerged > 1 and _shuffleEvents:
            random.shuffle(cDelays)

    mTimeBlock = (
        prd.TimeBlock(id=_cTime, prompt_events=_cPrompts, delayed_events=cDelays),
    )

    return mTimeBlock


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
        # When appending, start time is relative.
        relMode = True
    else:
        relMode = False

    iFiles, startTime = parseAcqArguments(args)
    writerOutput = defineWriter(args.oFile, args.verbose)
    fileIO, sTimeBlockId, oHeader = setupFileIO(iFiles, startTime, args.headerProvider)

    mFileNextTimeBlock = []
    timeBlockBuffer = []
    for i, cFileIO in enumerate(fileIO):
        fTimeBlock = next(cFileIO)
        mFileNextTimeBlock.append(fTimeBlock.id + sTimeBlockId[i])
        timeBlockBuffer.append(fTimeBlock)

    with prd.BinaryPrdExperimentWriter(writerOutput) as writer:
        writer.write_header(oHeader)
        while True:
            cPrompts = []
            cDelays = []
            nbMerged = 0
            removeFile = []

            if relMode:
                cTime = mFileNextTimeBlock[0]
                nbInputCandidates = 1
            else:
                cTime = min(mFileNextTimeBlock)
                nbInputCandidates = len(mFileNextTimeBlock)

            for i in range(nbInputCandidates):
                if mFileNextTimeBlock[i] <= cTime:
                    cTimeBlock = timeBlockBuffer[i]
                    cPrompts.extend(cTimeBlock.prompt_events)
                    if cTimeBlock.delayed_events is not None:
                        cDelays.extend(cTimeBlock.delayed_events)
                    nbMerged += 1
                    # Update info
                    try:
                        timeBlockBuffer[i] = next(fileIO[i])
                        mFileNextTimeBlock[i] = timeBlockBuffer[i].id + sTimeBlockId[i]
                    except StopIteration:
                        removeFile.append(i)

            mTimeBlock = createTimeBlock(
                cTime, cPrompts, cDelays, nbMerged, args.shuffleEvents
            )
            writer.write_time_blocks(mTimeBlock)

            if len(removeFile) != 0:
                # Pop in reverse order to not break anything
                for cPos in removeFile[::-1]:
                    fileIO.pop(cPos)
                    endTime = mFileNextTimeBlock.pop(cPos)
                    timeBlockBuffer.pop(cPos)
                    sTimeBlockId.pop(cPos)

                if relMode and len(sTimeBlockId) != 0:
                    # Since the current file is finished, we now know its endtime and
                    # can adjust the start time of the other parts in consequence
                    sTimeBlockId = [cStartTime + endTime for cStartTime in sTimeBlockId]
            # If any file are remaining, get the next time block ID
            if len(fileIO) == 0:
                break
