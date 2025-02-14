# OpenMSUtils

This open source project is used for easily reading and writing MS files and Fasta files.

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
this package provides various classes for reading MS files.
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

