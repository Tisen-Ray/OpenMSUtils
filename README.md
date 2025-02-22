# OpenMSUtils

This open source project is used for easily reading and processing MS files and Fasta files.

## Usage

first, install the package, you can use pip to install the package

```bash
pip install git+https://github.com/Elcherneske/OpenMSUtils.git
```

or

```bash
git clone https://github.com/Elcherneske/OpenMSUtils.git
cd OpenMSUtils
pip install .
```

### Read MS file
this package provides various classes for reading MS files, including MZML, MGF, MS1, MS2.

Here is an example of reading MS file:
```python
from OpenMSUtils.SpectraUtils import MZMLReader, MGFReader, MS1Reader, MS2Reader

reader = MZMLReader()
meta_data, spectrum = reader.read(file_path)

reader = MGFReader()
meta_data, spectrum = reader.read(file_path)

reader = MS1Reader()
meta_data, spectrum = reader.read(file_path)

reader = MS2Reader()
meta_data, spectrum = reader.read(file_path)

# get peaks from spectrum
peaks = spectrum.peaks
print(peaks)

# get precursor from spectrum
precursor = spectrum.precursor
print(precursor)

# get scan_info from spectrum
scan_info = spectrum.scan_info
print(scan_info)

# get ms level from spectrum
ms_level = spectrum.level
print(ms_level)

# get additional_info from spectrum
additional_info = spectrum.additional_info
print(additional_info)

```

### ion mobility spectrum
this package provides various classes for reading and processing ion mobility spectrum

Here is an example of reading ion mobility spectrum:

```python
from OpenMSUtils.SpectraUtils import MZMLReader, SpectrumPlotter, IonMobilityUtils

reader = MZMLReader()
meta_data, spectra = reader.read(file_path)

ion_mobility_utils = IonMobilityUtils()
ion_mobility_utils.get_ion_mobility(spectra[start_index:end_index])

plotter = SpectrumPlotter()
plotter.plot_ion_mobility(ion_mobility_utils.ion_mobility_spectrum, time_range=(0, 100), mz_range=(0, 1000), time_bins=200, mz_bins=200)

```



### Read Fasta file && Write Fasta file

```python
from OpenMSUtils.FastaUtils import FastaReader, FastaWriter

reader = FastaReader()
sequences = reader.read(file_path)

#sequences: {head: sequence, ...}
writer = FastaWriter()
writer.write(sequences, file_path)
```

### Nucleic Acid
This package provides various classes for processing nucleic acid sequences, including oligonucleotide sequences, DNA sequences, and RNA sequences.

Here is an example of processing nucleic acid sequences:

```python
from OpenMSUtils.MolecularUtils import NucleicAcidUtils

# generate a oligonucleotide sequence
sequence = NucleicAcidUtils.Oligonucleotide("ATCG")

# add modifications to the sequence
sequence.add_modification(0, NucleicAcidUtils.Modification("Phosphorylation", "HPO3"))

# add end modifications to the sequence
sequence.add_end_modifications(("Phosphorylation", "HPO3"), ("Phosphorylation", "HPO3"))

# set charge of the sequence
sequence.set_charge(1)

# set adduct of the sequence
sequence.set_adduct("H+")

# generate fragments of oligonucleotide
fragments = sequence.fragments

# get the mass of the sequence
mass = sequence.mass

```

