from lxml import etree

class CVParam(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._attrib = None
            return
        
        self._attrib = etree_element.attrib

    @property
    def attrib(self):
        return self._attrib

    @attrib.setter
    def attrib(self, attrib):
        self._attrib = attrib
    
    def to_xml(self) -> etree._Element:
        element = etree.Element("cvParam")
        for key, value in self._attrib.items():
            element.set(key, value)
        return element

class UserParam(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._attrib = None
            return
        
        self._attrib = etree_element.attrib
    
    @property
    def attrib(self):
        return self._attrib

    @attrib.setter
    def attrib(self, attrib):
        self._attrib = attrib
    
    def to_xml(self) -> etree._Element:
        element = etree.Element("userParam")
        for key, value in self._attrib.items():
            element.set(key, value)
        return element
