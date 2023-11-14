# date: 2023-11-14
# Author: Geprgios Soultanidis
# version: 0.01

# Usage: python split_to_respiratory_gates.py <input_file> <number_of_gates> <minimum_respiratory_amplitude> <maximum_respiratory_amplitude>
# Amplitude based respiratory gating, where the user defines the number of gates, the minimum and maximum respiratory amplitude
# The script reads the physio data from a csv file and assigns a gate to each event based on the respiratory amplitude
# TODO the script will be updated to read the physio data from the raw data file, fully in sinc with the packet time stamps

# Currently hard-wire location of generated files. This will need to change!
import sys

sys.path.append("../PETSIRD/python/")
import math
import numpy as np
import prd


# function to open a csv file and read time stamps (first column) and respiratory_amplitude (second column) and return them into two arrays (time_stamps, respiratory_amplitude)
# TODO: make this obsolete by reading the physio data from the raw data file
def read_csv_file(csv_file: str):
    time_stamps = []
    respiratory_amplitude = []
    with open(csv_file, "r") as f:
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            time_stamps.append(float(line.split(",")[0]))
            respiratory_amplitude.append(float(line.split(",")[1]))
    return np.array(time_stamps), np.array(respiratory_amplitude)


def asign_gate(
    respiratory_amplitude: float,
    number_of_gates: int,
    minimum_resp_amplitude: float,
    maximum_resp_amplitude: float,
) -> int:
    gate = math.floor(
        (respiratory_amplitude * number_of_gates)
        / (maximum_resp_amplitude - minimum_resp_amplitude)
    )
    return gate


if __name__ == "__main__":
    # check if the number of arguments is correct
    if len(sys.argv) != 5:
        print(
            "Usage: python split_to_respiratory_gates.py <input_file> <number_of_gates> <minimum_respiratory_amplitude> <maximum_respiratory_amplitude>"
        )
        sys.exit(1)
    # asign the arguments to variables
    input_file = sys.argv[1]
    number_of_gates = int(sys.argv[2])
    minimum_respiratory_amplitude = float(sys.argv[3])
    maximum_respiratory_amplitude = float(sys.argv[4])
    # read the input file
    reader = prd.BinaryPrdExperimentReader(input_file)
    header = reader.read_header()
    # temporary print statements to check the header
    print(f"Subject ID: {header.exam.subject.id}")
    print(f"Number of detectors: {header.scanner.number_of_detectors()}")
    print(f"Number of TOF bins: {header.scanner.number_of_tof_bins()}")
    print(f"Number of energy bins: {header.scanner.number_of_energy_bins()}")

    # run the asign_gate function for each event and add the gate to the event
    all_events = asign_gate(
        254,
        number_of_gates,
        minimum_respiratory_amplitude,
        maximum_respiratory_amplitude,
    )
    # load the respirtatory signal TODO this part will be replaced with the in-packet physio data
    time_stamps, resp_amplitude = read_csv_file("physio/resp_sino.csv")
    # create acounter for the time stamps, where it starts with 0. TODO, this part will change, if physio is in-packet
    time_stamp_counter = 0
    # get all the time blocks and for each one, get the events
    for time_block in reader.read_time_blocks():
        # for now, we just assume that the first time block has the same time stamp with the first physio record
        time_stamp = (
            time_block.id * 0.001
        )  # the id are in msec and we convert them in seconds
        # compare the time stamp of the time block with the physio time stamp at the time_stamp_counter
        if time_stamp >= time_stamps[time_stamp_counter + 1]:
            # if the time stamp of the time block is bigger than the physio time stamp, increase the time_stamp_counter by 1
            time_stamp_counter += 1
        gate_indicator = asign_gate(
            resp_amplitude[time_stamp_counter],
            number_of_gates,
            minimum_respiratory_amplitude,
            maximum_respiratory_amplitude,
        )
        print(
            "time stamp is: ",
            time_stamp,
            " the amplitude is:",
            resp_amplitude[time_stamp_counter],
            "gate is: ",
            gate_indicator,
        )
