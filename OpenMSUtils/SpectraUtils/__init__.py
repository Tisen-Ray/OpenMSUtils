# Import high-performance Rust-backed implementations by default
try:
    from .MSObject_Rust import MSObject, MSObjectRust
    RUST_AVAILABLE = True
    print("Using high-performance Rust-backed MSObject")
except ImportError:
    from .MSObject import MSObject
    MSObjectRust = None
    RUST_AVAILABLE = False
    print("Using Python MSObject (Rust implementation not available)")

# Try to import Rust-backed MZML tools
try:
    from .MZMLUtils_Rust import MZMLReader, MZMLWriter
    print("Using high-performance Rust-backed MZMLReader")
except ImportError:
    from .MZMLUtils import MZMLReader, MZMLWriter
    print("Using Python MZMLReader (Rust implementation not available)")

# Other modules (still using Python implementations for now)
from .SpectraConverter import SpectraConverter
from .SpectraPlotter import SpectraPlotter
from .IonMobilityUtils import IonMobilityUtils
from .XICSExtractor import XICSExtractor, XICResult, FragmentIon, PolymerInfo
from .MGFUtils import MGFReader, MGFWriter
from .MSFileUtils import MSFileReader, MSFileWriter
from .SpectraSearchUtils import BinnedSpectra