from accurate_molmass import EnhancedFormula

class Nucleotide():
    def __init__(self, character, deoxidation=False):
        self.character = character
        self.deoxidation = deoxidation

    @property
    def mass(self):
        formula = EnhancedFormula("C5H8O6P")
        if self.character == "A":
            formula += EnhancedFormula("C5H4N5")
        elif self.character == "G":
            formula += EnhancedFormula("C5H4N5O")
        elif self.character == "C":
            formula += EnhancedFormula("C5H4N3O")
        elif self.character == "T":
            formula += EnhancedFormula("C5H5N2O2")
        elif self.character == "U":
            formula += EnhancedFormula("C5H3N2O2")

        if self.deoxidation:
            formula -= EnhancedFormula("O")

        return formula.mass
    
    @property
    def nucleobase(self):
        if self.character == "A":
            return EnhancedFormula("C5H4N5")
        elif self.character == "G":
            return EnhancedFormula("C5H4N5O")
        elif self.character == "C":
            return EnhancedFormula("C5H4N3O")
        elif self.character == "T":
            return EnhancedFormula("C5H5N2O2")
        elif self.character == "U":
            return EnhancedFormula("C5H3N2O2")
            
    
class Modification():
    def __init__(self, name: str, formula: str):
        self.name = name
        self.formula = formula

    @property
    def mass(self):
        if self.formula.startswith('@'):
            return -EnhancedFormula(self.formula[1:]).mass
        return EnhancedFormula(self.formula).mass

class Oligonucleotide():
    """
    Oligonucleotide class
    """
    sequence: str = None
    deoxidation: bool = False
    modifications: dict = {}
    charge: int = None
    adduct: float = None
    end_3_modification: Modification = None
    end_5_modification: Modification = None

    def __init__(self, sequence: str, deoxidation=False):
        """
        sequence: str (5' -> 3')
        """
        self.sequence = sequence
        self.deoxidation = deoxidation
        self.modifications = {}
    
    def add_end_modifications(self, end_3_modification, end_5_modification):
        end_3_name, end_3_formula = end_3_modification
        end_5_name, end_5_formula = end_5_modification

        self.end_3_modification = Modification(end_3_name, end_3_formula)
        self.end_5_modification = Modification(end_5_name, end_5_formula)
    
    def add_modification(self, index: int, modification: Modification):
        self.modifications[index] = modification
    
    def set_charge(self, charge: int):
        self.charge = charge
    
    def set_adduct(self, adduct: str):
        if adduct == "@H+":
            self.adduct = -EnhancedFormula("H+").mass
        elif adduct == "H+":
            self.adduct = EnhancedFormula("H+").mass
        elif adduct == "Na+":
            self.adduct = EnhancedFormula("Na+").mass
        elif adduct == "K+":
            self.adduct = EnhancedFormula("K+").mass
        elif adduct == "NH4+":
            self.adduct = EnhancedFormula("NH4+").mass
        else:
            raise ValueError(f"Invalid adduct: {adduct}")

    def generate_fragments(self, ion_type: str):
        ion_mod = {
            'a': -EnhancedFormula("HPO3").mass, 
            'a_B': -EnhancedFormula("HPO3").mass, 
            'b': -EnhancedFormula("HPO2").mass,
            'c': 0.0,
            'd': EnhancedFormula("O").mass,
            'w': EnhancedFormula("HPO3").mass, 
            'x': EnhancedFormula("HPO2").mass, 
            'y': 0.0, 
            'z': -EnhancedFormula("O").mass
        }

        fragments = []
        if ion_type in ["a", "a_B", "b", "c", "d"]:
            fragment_mass = self.end_5_modification.mass if self.end_5_modification else 0.0
            for i, nucleotide in enumerate(self.sequence):
                fragment_mass += Nucleotide(nucleotide, self.deoxidation).mass
                if i in self.modifications:
                    fragment_mass += self.modifications[i].mass
                # Skip record the first and last nucleotide
                if i == 0 or i == len(self.sequence) - 1:
                    continue
                fragments.append(fragment_mass + ion_mod[ion_type])
        elif ion_type in ["w", "x", "y", "z"]:
            fragment_mass = self.end_3_modification.mass if self.end_3_modification else 0.0
            for i in reversed(range(len(self.sequence))):
                nucleotide = self.sequence[i]
                fragment_mass += Nucleotide(nucleotide, self.deoxidation).mass
                if i in self.modifications:
                    fragment_mass += self.modifications[i].mass
                # Skip record the first and last nucleotide
                if i == 0 or i == len(self.sequence) - 1:
                    continue
                fragments.append(fragment_mass + ion_mod[ion_type])

        return fragments
    
    @property
    def mass(self):
        mass = self.end_5_modification.mass if self.end_5_modification else 0.0
        for i, nucleotide in enumerate(self.sequence):
            mass += Nucleotide(nucleotide, self.deoxidation).mass
            if i in self.modifications:
                mass += self.modifications[i].mass
        mass += self.end_3_modification.mass if self.end_3_modification else 0.0
        return mass
    
    @property
    def fragments(self):
        fragments = {}
        adduct = self.adduct if self.adduct is not None else -EnhancedFormula("H+").mass
        charge = self.charge if self.charge is not None else -1
        if not (adduct < 0 and charge < 0) or (adduct > 0 and charge > 0):
            raise ValueError(f"Invalid adduct/charge combination: adduct={adduct}, charge={charge}")
            
        charge_sign = 1 if charge > 0 else -1
        max_fragment_charge = abs(charge)

        for ion_type in ["a", "b", "c", "d", "w", "x", "y", "z"]:
            fragment_masses = self.generate_fragments(ion_type)
            if max_fragment_charge == 1:
                max_fragment_charge = 2
            for z in range(1, max_fragment_charge):
                charge_symbol = '+' if charge_sign > 0 else '-'
                fragment_key = f"{ion_type}{z}{charge_symbol}"
                # Calculate m/z values for each fragment mass
                fragments[fragment_key] = [(mass + z * adduct) / z for mass in fragment_masses]

        return fragments
        
                

if __name__ == "__main__":
    print(Nucleotide("A").mass)
    print(Nucleotide("G").mass)
    print(Nucleotide("C").mass)
    print(Nucleotide("T").mass)
    print(Nucleotide("U").mass)
    oligo = Oligonucleotide("AACGU")
    oligo.add_end_modifications(("end3", "OH"), ("end5", "H"))
    oligo.set_charge(-3)
    print(oligo.mass)
    print(oligo.fragments)
    print(Oligonucleotide("AACGU").mass)

