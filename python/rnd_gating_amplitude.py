# date: 2023-11-14
# Author: Georgios Soultanidis
# Affiliation: BMEII, Icahn School of Medicine at Mount Sinai
# version: 0.1

# Usage: python rnd_gating_amplitude.py <input_file> <number_of_gates> <minimum_physio_1_amplitude> <maximum_physio_1_amplitude>
# Amplitude based physio_1 gating, where the user defines the number of gates, the minimum and maximum physio_1 amplitude
# The script reads the physio data from a csv file and assigns a gate to each event based on the physio_1 amplitude
# TODO the script will be updated to read the physio data from the raw data file, fully in sinc with the packet time stamps

# Currently hard-wire location of generated files. This will need to change!
import sys

sys.path.append("../PETSIRD/python/")
import math
import numpy as np
import petsird


# function to open a csv file and read time stamps (first column) and physio_1_amplitude (second column) and return them into two arrays (time_stamps, physio_1_amplitude)
# TODO: make this obsolete by reading the physio data from the raw data file
def read_csv_file(csv_file: str):
    time_stamps = []
    physio_amplitude = []
    with open(csv_file, "r") as f:
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            time_stamps.append(float(line.split(",")[0]))
            physio_amplitude.append(float(line.split(",")[1]))
    return np.array(time_stamps), np.array(physio_amplitude)


def asign_gate(
    physio_amplitude: float,
    number_of_gates: int,
    minimum_physio_amplitude: float,
    maximum_physio_amplitude: float,
) -> int:
    gate = math.floor(
        (physio_amplitude * number_of_gates)
        / (maximum_physio_amplitude - minimum_physio_amplitude)
    )
    return gate


if __name__ == "__main__":
    # check if the number of arguments is correct
    if len(sys.argv) != 5:
        print(
            "Usage: python split_to_physio_1_gates.py <input_file> <number_of_gates> <minimum_physio_1_amplitude> <maximum_physio_1_amplitude>"
        )
        sys.exit(1)
    # asign the arguments to variables
    input_file = sys.argv[1]
    number_of_gates = int(sys.argv[2])
    minimum_physio_1_amplitude = float(sys.argv[3])
    maximum_physio_1_amplitude = float(sys.argv[4])
    # read the input file
    reader = petsird.BinaryPETSIRDReader(input_file)
    header = reader.read_header()
    # temporary print statements to check the header
    print(f"Subject ID: {header.exam.subject.id}")
    print(f"Number of detectors: {header.scanner.number_of_detectors()}")
    print(f"Number of TOF bins: {header.scanner.number_of_tof_bins()}")
    print(f"Number of energy bins: {header.scanner.number_of_energy_bins()}")

    # load the physio signal TODO this part will be replaced with the in-packet physio data
    time_stamps, physio_1_amplitude = read_csv_file("physio/resp_sino.csv")
    # create acounter for the time stamps, where it starts with 0. TODO, this part will change, if physio is in-packet.
    time_stamp_counter = 0
    # initiallize the writer. we open the generalized "writers" as a dynamic system that can change with the number of gates provided by the user
    writers = [
        petsird.BinaryPETSIRDWriter(f"gate_physio_1_{i}.raw")
        for i in range(0, number_of_gates)
    ]
    for writer_gate in writers:
        writer_gate.write_header(header)

    # writer = petsird.BinaryPETSIRDWriter("test.raw")
    # writer.write_header(header)

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
            physio_1_amplitude[time_stamp_counter],
            number_of_gates,
            minimum_physio_1_amplitude,
            maximum_physio_1_amplitude,
        )

        # each gate that has been indicated will be written to a different file name
        writers[gate_indicator].write_time_blocks([time_block])

    for writer_gate in writers:
        writer_gate.close()
