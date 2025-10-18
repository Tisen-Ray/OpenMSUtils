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
This package provides various classes for reading MS files, including MZML, MGF, MS1, and MS2.

Here is a detailed example of reading an MS file using `MZMLReader` and converting the spectra to `MSObject` using `SpectraConverter`:

```python
from OpenMSUtils.SpectraUtils import MZMLReader, SpectraConverter

# Step 1: Initialize the MZMLReader
reader = MZMLReader()

# Step 2: Specify the path to your mzML file
file_path = "path/to/your/test.mzML"

# Step 3: Read the mzML file
# You can choose to parse spectra in parallel for better performance
mzml_obj = reader.read(file_path, parse_spectra=True, parallel=True)

# Step 4: Access the spectra from the MZMLObject
if mzml_obj.run and mzml_obj.run.spectra_list:
    print(f"成功读取 {len(mzml_obj.run.spectra_list)} 个谱图")

    # Step 5: Iterate through the spectra and convert them to MSObject
    ms_objects = []
    for spectrum in mzml_obj.run.spectra_list:
        ms_obj = SpectraConverter.to_msobject(spectrum)
        ms_objects.append(ms_obj)
    print(f"转换成功: {spectrum.attrib.get('id', 'N/A')} -> MSObject")

    # Step 6: Access properties of the MSObject
    for ms_obj in ms_objects:
    print(f"MS级别: {ms_obj.level}")
    print(f"保留时间: {ms_obj.retention_time:.2f}秒")
    print(f"峰值数量: {len(ms_obj.peaks)}")
else:
    print("未读取到谱图数据")
```

Here is an example of using MSObject
```python
from OpenMSUtils.SpectraUtils import MSObject, SpectraConverter

ms_object = SpectraConverter.to_msobject(spectrum)

# get peaks from ms_object
peaks = ms_object.peaks

# get precursor from ms_object
precursor = ms_object.precursor

# get scan_info from ms_object
scan_info = ms_object.scan

# get ms level from ms_object
ms_level = ms_object.level

# get additional_info from ms_object
additional_info = ms_object.additional_info

# get scan_number from ms_object
scan_number = ms_object.scan_number

# get retention_time from ms_object
retention_time = ms_object.retention_time

```

Here is an example of reading MS file from mgf, ms1, ms2:
```python
from OpenMSUtils.SpectraUtils import MZMLReader, MGFReader, MS1Reader, MS2Reader

reader = MGFReader()
meta_data, spectrum = reader.read(file_path)

reader = MS1Reader()
meta_data, spectrum = reader.read(file_path)

reader = MS2Reader()
meta_data, spectrum = reader.read(file_path)

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

