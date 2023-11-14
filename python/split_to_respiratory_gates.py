# Currently hard-wire location of generated files. This will need to change!
import sys

sys.path.append("../PETSIRD/python/")
import math
import numpy as np
import prd

# open a csv file and read time stamps (first column) and respiratory_amplitude (second column)


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
    print("this goes to this gate:", all_events)
