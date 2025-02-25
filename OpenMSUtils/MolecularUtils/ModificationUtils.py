from .accurate_molmass import EnhancedFormula
import os
import pandas as pd

class Modification():
    def __init__(self, name: str, formula: str):
        self.name = name
        self.formula = formula

    @property
    def mass(self):
        parts = self.formula.split('@')
        if len(parts) == 1:
            return EnhancedFormula(parts[0]).isotope.mass
        elif len(parts) == 2 and parts[1]:  # Ensure there is something after '@'
            return EnhancedFormula(parts[0]).isotope.mass - EnhancedFormula(parts[1]).isotope.mass
        else:
            raise ValueError(f"Invalid formula: {self.formula}")

class ProteinModificationRepository():
    def __init__(self):
        self.modifications = None
    
    def load(self, file_path: str):
        if os.path.exists(file_path):
            self.modifications = pd.read_csv(file_path, sep='\t').to_dict(orient='records')
        else:
            raise FileNotFoundError(f"File {file_path} not found")
        
    def find(self, mass: float, tolerance: float = 0.0001) -> list[Modification]:
        results = []
        for modification in self.modifications:
            if abs(modification['Isotopic Mass'] - mass) <= tolerance:
                results.append(Modification(modification['Mod Name'], modification['Formula']))
        return None

