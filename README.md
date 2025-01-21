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

```python
from SpectraUtils.MZMLReader import MZMLReader

reader = MZMLReader()
```

