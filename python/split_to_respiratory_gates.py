# Currently hard-wire location of generated files. This will need to change!
import sys

sys.path.append("../PETSIRD/python/")
import math
import numpy as np
import prd

# function that gets the respiratory position (between 0 and 255) and asign it into a gate given a number of gates


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
    input_file = sys.argv[1]
    number_of_gates = int(sys.argv[2])
    minimum_respiratory_amplitude = float(sys.argv[3])
    maximum_respiratory_amplitude = float(sys.argv[4])

    reader = prd.BinaryPrdExperimentReader(input_file)
    header = reader.read_header()
    print(f"Subject ID: {header.exam.subject.id}")
    print(f"Number of detectors: {header.scanner.number_of_detectors()}")
    print(f"Number of TOF bins: {header.scanner.number_of_tof_bins()}")
    print(f"Number of energy bins: {header.scanner.number_of_energy_bins()}")

    # run the asign_gate function for each event and add the gate to the event
    all_events = asign_gate(
        number_of_gates,
        number_of_gates,
        minimum_respiratory_amplitude,
        maximum_respiratory_amplitude,
    )
