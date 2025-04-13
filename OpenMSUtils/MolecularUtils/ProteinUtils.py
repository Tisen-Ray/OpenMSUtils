from .accurate_molmass import EnhancedFormula
from .ModificationUtils import Modification

class AminoAcid():
    """
    Amino acid class
    """
    AA_formula = {
        "A": "C3H5NO", #Alanine
        "C": "C3H5NOS", #Cysteine
        "D": "C4H5NO3", #Aspartic acid
        "E": "C5H7NO3", #Glutamic acid
        "F": "C9H9NO", #Phenylalanine
        "G": "C2H3NO", #Glycine
        "H": "C6H7N3O", #Histidine
        "I": "C6H11NO", #Isoleucine
        "K": "C6H12N2O", #Lysine
        "L": "C6H11NO", #Leucine
        "M": "C5H9NOS", #Methionine
        "N": "C4H6N2O2", #Asparagine
        "P": "C5H7NO", #Proline
        "Q": "C5H8N2O2", #Glutamine
        "R": "C6H12N4O", #Arginine
        "S": "C3H5NO2", #Serine
        "T": "C4H7NO2", #Threonine
        "U": "C3H5NOSe", #selenocysteine
        "V": "C5H9NO", #Valine
        "W": "C11H10N2O", #Tryptophan
        "Y": "C9H9NO2", #Tyrosine
    }
    def __init__(self, character: str):
        self.character = character

    @property
    def mass(self):
        if self.character not in self.AA_formula:
            raise ValueError(f"Invalid amino acid: {self.character}")
        formula = EnhancedFormula(self.AA_formula[self.character])
        return formula.isotope.mass

class Peptide():
    def __init__(self, sequence: str):
        """
        sequence: str (N-terminus -> C-terminus)
        """
        self._sequence = sequence
        self._modifications = {}
        self._charge = 0
        self._adduct_mass = None
        self._end_C_modification = None
        self._end_N_modification = None
        self._fragments_type = None
    
    def set_end_modifications(self, end_C_modification: tuple[str, str], end_N_modification: tuple[str, str]):
        end_C_name, end_C_formula = end_C_modification
        end_N_name, end_N_formula = end_N_modification

        self._end_C_modification = Modification(end_C_name, end_C_formula)
        self._end_N_modification = Modification(end_N_name, end_N_formula)
    
    def add_modification(self, index: int, modification: Modification):
        self._modifications[index] = modification
    
    def set_charge(self, charge: int):
        self._charge = charge
    
    def set_adduct(self, adduct: str):
        adduct_modification = Modification('adduct', adduct)
        self._adduct_mass = adduct_modification.mass
    
    def set_fragments_type(self, fragments_type: list[str]):
        for fragment_type in fragments_type:
            if fragment_type not in ["a", "b", "c", "x", "y", "z"]:
                raise ValueError(f"Invalid fragment type: {fragment_type}")
        self._fragments_type = fragments_type

    @property
    def mass(self):
        self._check()
        total_mass = sum(AminoAcid(aa).mass for aa in self._sequence)
        for index, modification in self._modifications.items():
            total_mass += modification.mass
        total_mass += self._end_C_modification.mass if self._end_C_modification else 0.0
        total_mass += self._end_N_modification.mass if self._end_N_modification else 0.0
        return total_mass

    @property
    def mz(self):
        self._check()
        if self._charge == 0 or self._adduct_mass is None:
            return self.mass
        else:
            return (self.mass + self._adduct_mass) / self._charge

    @property
    def fragments(self):
        self._check()
        adduct_mass = self._adduct_mass if self._adduct_mass is not None else EnhancedFormula("H+").isotope.mass
        charge = self._charge if self._charge is not None else 1
        fragments_type = self._fragments_type if self._fragments_type is not None else ["b", "y"]
        charge_sign = 1 if charge > 0 else -1
        max_fragment_charge = abs(charge)

        fragments = {}
        for ion_type in fragments_type:
            fragment_masses = self._generate_fragments(ion_type)
            if max_fragment_charge == 1:
                max_fragment_charge = 2
            for z in range(1, max_fragment_charge):
                charge_symbol = '+' if charge_sign > 0 else '-'
                fragment_key = f"{ion_type}{z}{charge_symbol}"
                # Calculate m/z values for each fragment mass
                fragments[fragment_key] = [(mass + z * adduct_mass) / z for mass in fragment_masses]

        return fragments
    
    def _generate_fragments(self, ion_type: str):
        ion_mod = {
            'a': -EnhancedFormula("CO").isotope.mass, 
            'b': 0.0,
            'c': EnhancedFormula("NH").isotope.mass,
            'x': EnhancedFormula("CO").isotope.mass, 
            'y': 0.0, 
            'z': -EnhancedFormula("NH").isotope.mass
        }

        fragments = []
        if ion_type in ["a", "b", "c"]:
            fragment_mass = self._end_N_modification.mass if self._end_N_modification else 0.0
            for i, nucleotide in enumerate(self._sequence):
                fragment_mass += AminoAcid(nucleotide).mass
                if i in self._modifications:
                    fragment_mass += self._modifications[i].mass
                # Skip record the first and last nucleotide
                if i == 0 or i == len(self._sequence) - 1:
                    continue
                fragments.append(fragment_mass + ion_mod[ion_type])

        elif ion_type in ["x", "y", "z"]:
            fragment_mass = self._end_C_modification.mass if self._end_C_modification else 0.0
            for i in reversed(range(len(self._sequence))):
                nucleotide = self._sequence[i]
                fragment_mass += AminoAcid(nucleotide).mass
                if i in self._modifications:
                    fragment_mass += self._modifications[i].mass
                # Skip record the first and last nucleotide
                if i == 0 or i == len(self._sequence) - 1:
                    continue
                fragments.append(fragment_mass + ion_mod[ion_type])

        return fragments
        
    def _check(self):
        if self._charge == 0:
            print("Charge is 0, default to +1")
            self._charge = 1

        if self._adduct_mass is None:
            print("Adduct is None, default to H+")
            self._adduct_mass = EnhancedFormula("H+").isotope.mass

        if self._fragments_type is None:
            print("Fragments type is None, default to b,y")
            self._fragments_type = ["b", "y"]
        
        if self._end_C_modification is None:
            print("End C modification is None, default to None")
            self._end_C_modification = None

        if self._end_N_modification is None:
            print("End N modification is None, default to None")
            self._end_N_modification = None

if __name__ == "__main__":
    from accurate_molmass import EnhancedFormula
    formula = EnhancedFormula("Se")
    print(formula.isotope)
