# date: 2025-07-17
# Author: Georgios Soultanidis
# Affiliation: BMEII, Icahn School of Medicine at Mount Sinai
# version: 0.3

# The functionality of this script is to append physiological signals (e.g., ECG) to a PETSIRD file.
# you have to provide a PETSIRD file and a CSV file with two columns: [start_time_ms, value].
# The script will read the CSV file and create an ExternalSignalTimeBlock for each row,
# which will be appended to the PETSIRD file.
# The output will be a new PETSIRD file with the appended physiological signals.

# TODO: Right now, the id of the physiological signal is hardcoded to 1.
# You may want to change this if you have multiple physiological signals. 


#the way to run this script is:
# python append_physio.py -i input.petsird -o output.petsird -p physio.csv
# where input.petsird is the input PETSIRD file, output.petsird is the output PETSIRD file,
# and physio.csv is the CSV file with the physiological signals


import petsird
import pandas as pd
import argparse

# Define signal type mapping
signal_type_map = {
    "ecg_trace": petsird.ExternalSignalTypeEnum.ECG_TRACE,
    "ecg_trigger": petsird.ExternalSignalTypeEnum.ECG_TRIGGER,
    "resp_trace": petsird.ExternalSignalTypeEnum.RESP_TRACE,
    "resp_trigger": petsird.ExternalSignalTypeEnum.RESP_TRIGGER,
    "other": petsird.ExternalSignalTypeEnum.OTHER,
    "other_motion_signal": petsird.ExternalSignalTypeEnum.OTHER_MOTION_SIGNAL,
    "other_motion_trigger": petsird.ExternalSignalTypeEnum.OTHER_MOTION_TRIGGER,
}

def parserCreator():
    parser = argparse.ArgumentParser(
        prog="append_physio",
        description="Append physiological signals to a PETSIRD file",
    )
    parser.add_argument(
        "-i", "--input", type=str, required=True, help="Input PETSIRD file"
    )
    parser.add_argument(
        "-o", "--output", type=str, required=True, help="Output PETSIRD file"
    )
    parser.add_argument(
        "-p",
        "--physio",
        type=str,
        required=True,
        help="Physiological data file (CSV with start_time_ms,value)",
    )
    parser.add_argument(
        "-t",
        "--signal-type",
        type=str,
        required=True,
        default="other_motion_signal",
        help=f"Signal type to use. Options: {', '.join(signal_type_map.keys())}",
    )
    return parser.parse_args()


args = parserCreator()

# Validate signal type
signal_type_key = args.signal_type.lower()
if signal_type_key not in signal_type_map:
    raise ValueError(f"Invalid signal type: {signal_type_key}. Valid options are: {list(signal_type_map.keys())}")
signal_enum = signal_type_map[signal_type_key]

# Read CSV with two columns: [start_time_ms, value]
df = pd.read_csv(args.physio, header=None)
starts_ms = df.iloc[:, 0].astype(int).values
values = df.iloc[:, 1].astype(int).values

physio_id = 1  # must be unique and consistent with your data

# Open reader and writer
with petsird.BinaryPETSIRDReader(args.input) as reader, open(
    args.output, "wb"
) as out_file, petsird.BinaryPETSIRDWriter(out_file) as writer:

    # Read and modify header
    header = reader.read_header()

    if not any(sig.id == physio_id for sig in header.exam.external_signals):
        physio_signal = petsird.ExternalSignal(
            type=signal_enum,
            description="Signal from CSV (2-column format)",
            id=physio_id,
        )
        header.exam.external_signals.append(physio_signal)

    # Write modified header
    writer.write_header(header)

    # Copy all time blocks
    for block in reader.read_time_blocks():
        writer.write_time_blocks((block,))

    # Inject one ExternalSignalTimeBlock per row
    for t_ms, val in zip(starts_ms, values):
        time_interval = petsird.TimeInterval(start=int(t_ms), stop=int(t_ms + 1))
        physio_block = petsird.ExternalSignalTimeBlock(
            time_interval=time_interval,
            signal_id=physio_id,
            signal_values=[val],
        )
        writer.write_time_blocks(
            (petsird.TimeBlock.ExternalSignalTimeBlock(physio_block),)
        )
