from .MSObject import MSObject

class IonMobilityUtils:
    def __init__(self):
        self._ion_mobility_spectrum = {}

    def get_ion_mobility(self, ms_object_list: list[MSObject]):
        for ms_object in ms_object_list:
            drift_time = ms_object.scan.drift_time
            if drift_time is not None and drift_time >= 0:
                if self._ion_mobility_spectrum.get(drift_time) is None:
                    self._ion_mobility_spectrum[drift_time] = ms_object.peaks
                else:
                    self._ion_mobility_spectrum[drift_time].extend(ms_object.peaks)

    @property
    def ion_mobility_spectrum(self):
        return self._ion_mobility_spectrum

