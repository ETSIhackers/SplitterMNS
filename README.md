# PETSIRD use case: split and merge dataset

The purpose of this repo is to provide splitting and merging capabilities for datasets saved in the PETSIRD format.



## Background
The [Emission Tomography Standardization Initiative (ETSI)](https://etsinitiative.org/)
is working towards establishing a standard for PET Raw Data, called PETSIRD ("PET ETSI Raw Data").

The specification uses the [yardl](https://aka.ms/yardl) tool to define the model. `yardl` can be
used to read the specification (in the `model` directory) and generate an PI for both C++ and API to read/write PETSIRD data.

This use case was started at the start of November 2023 from a draft model of PETSIRD which is defined in https://github.com/ETSInitiative/PRDdefinition.

CAVEAT: the draft model generates code in the `prd` namespace. Nevertheless, we have used the name PETSIRD here
in most places (except where needed).

## Current capabilities
Three tools are currently available. All of them are only in python right now.

### rnd_sampler
Enable the generation of a noisier instance of a dataset by either dropping times block or events.

### merger
Merge multiple datasets in one dataset.
`(Un-tested right now, might or might not work...)`

### rnd_gating_amplitude
Reads the physio data from a csv file and assigns a gate to each event based on the physio_1 amplitude.



## How to use this repo

1. Open the repo in [GitHub Codespaces](https://code.visualstudio.com/docs/remote/codespaces) or in a [VS Code devcontainer](https://code.visualstudio.com/docs/devcontainers/containers).
This codespace/container will contain all necessary tools, including `yardl` itself, as well as your repository.
2. Use `yardl` to generate C++ and Python code for the model:
  ```sh
  cd YourRepoName
  cd PETSIRD/model
  yardl generate
  cd ../..
  ```
3. See the help of the script of interest in the python folder for further explanation. (Currently, the cpp equivalent or unavailable.)
