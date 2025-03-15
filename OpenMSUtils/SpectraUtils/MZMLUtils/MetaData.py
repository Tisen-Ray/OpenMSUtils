from lxml import etree
from .ParamObject import CVParam, UserParam

class CVObject(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._id = None
            self._fullName = None
            self._version = None
            self._URI = None
            return
        
        self._id = etree_element.get("id")
        self._fullName = etree_element.get("fullName")
        self._version = etree_element.get("version")
        self._URI = etree_element.get("URI")
    
    @property
    def id(self):
        return self._id
    
    @property
    def fullName(self):
        return self._fullName
    
    @property
    def version(self):
        return self._version
    
    @property
    def URI(self):
        return self._URI
        
    def to_xml(self) -> etree._Element:
        element = etree.Element("cv")
        element.set("id", self._id)
        element.set("fullName", self._fullName)
        element.set("version", self._version)
        element.set("URI", self._URI)
        return element

class ProcessingMethod(object):
    def __init__(self, etree_element: etree._Element = None, order:int = None, software_ref:str = None):
        if etree_element is None:
            self._order = order
            self._software_ref = software_ref
            self._cv_params = []
            self._user_params = []
            return
            
        self._order = int(etree_element.get("order"))
        self._software_ref = etree_element.get("softwareRef")
        self._cv_params = []
        self._user_params = []
        
        for param in etree_element.findall("cvParam"):
            self._cv_params.append(CVParam(param))
        for param in etree_element.findall("userParam"):
            self._user_params.append(UserParam(param))
    
    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
        
    @property
    def order(self):
        return self._order
    
    @property
    def software_ref(self):
        return self._software_ref
    
    @property
    def cv_params(self):
        return self._cv_params
    
    @property
    def user_params(self):
        return self._user_params
        
    def to_xml(self) -> etree._Element:
        element = etree.Element("processingMethod")
        element.set("order", str(self._order))
        element.set("softwareRef", self._software_ref)
        
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
            
        return element

class DataProcessing(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._id = None
            self._processing_methods = []
            return
            
        self._id = etree_element.get("id")
        self._processing_methods = []
        for method in etree_element.findall("processingMethod"):
            self._processing_methods.append(ProcessingMethod(method))
    
    def add_processing_method(self, method:ProcessingMethod):
        self._processing_methods.append(method)
        
    @property
    def id(self):
        return self._id
    
    @property
    def processing_methods(self):
        return self._processing_methods
        
    def to_xml(self) -> etree._Element:
        element = etree.Element("dataProcessing")
        element.set("id", self._id)
        for method in self._processing_methods:
            element.append(method.to_xml())
        return element

class FileContent(object):
    def __init__(self, etree_element: etree._Element = None):
        self._cv_params = []
        self._user_params = []
        
        if etree_element is None:
            return
            
        for param in etree_element.findall("cvParam"):
            self._cv_params.append(CVParam(param))
        for param in etree_element.findall("userParam"):
            self._user_params.append(UserParam(param))
    
    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
    
    @property
    def cv_params(self):
        return self._cv_params

    @property
    def user_params(self):
        return self._user_params
        
    def to_xml(self) -> etree._Element:
        element = etree.Element("fileContent")
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
        return element

class SourceFile(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._id = None
            self._name = None
            self._location = None
            self._cv_params = []
            self._user_params = []
            return
            
        self._id = etree_element.get("id")
        self._name = etree_element.get("name")
        self._location = etree_element.get("location")
        self._cv_params = []
        self._user_params = []
        for param in etree_element.findall("cvParam"):
            self._cv_params.append(CVParam(param))
        for param in etree_element.findall("userParam"):
            self._user_params.append(UserParam(param))
    
    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
        
    @property
    def id(self):
        return self._id
    
    @property
    def name(self):
        return self._name
    
    @property
    def location(self):
        return self._location
    
    @property
    def cv_params(self):
        return self._cv_params

    @property
    def user_params(self):
        return self._user_params
        
    def to_xml(self) -> etree._Element:
        element = etree.Element("sourceFile")
        element.set("id", self._id)
        element.set("name", self._name)
        element.set("location", self._location)
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
        return element

class FileDescription(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._file_content = None
            self._source_files = []
            return
            
        self._file_content = FileContent(etree_element.find("fileContent"))
        self._source_files = []
        source_file_list = etree_element.find("sourceFileList")
        if source_file_list is not None:
            for source_file in source_file_list.findall("sourceFile"):
                self._source_files.append(SourceFile(source_file))
    
    def add_source_file(self, source_file:SourceFile):
        self._source_files.append(source_file)
        
    @property
    def file_content(self):
        return self._file_content
    
    @property 
    def source_files(self):
        return self._source_files
        
    def to_xml(self) -> etree._Element:
        element = etree.Element("fileDescription")
        element.append(self._file_content.to_xml())
        if len(self._source_files) > 0:
            source_file_list = etree.SubElement(element, "sourceFileList")
            source_file_list.set("count", str(len(self._source_files)))
            for source_file in self._source_files:
                source_file_list.append(source_file.to_xml())
        return element

class Component(object):
    def __init__(self, etree_element: etree._Element = None, order:int = None):
        if etree_element is None:
            self._order = order
            self._cv_params = []
            self._user_params = []
            return
            
        self._order = int(etree_element.get("order"))
        self._cv_params = []
        self._user_params = []
        for param in etree_element.findall("cvParam"):
            self._cv_params.append(CVParam(param))
        for param in etree_element.findall("userParam"):
            self._user_params.append(UserParam(param))
    
    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
        
    @property
    def order(self):
        return self._order
    
    @property
    def cv_params(self):
        return self._cv_params

    @property
    def user_params(self):
        return self._user_params
        
    def to_xml(self) -> etree._Element:
        element = etree.Element("component")
        element.set("order", str(self._order))
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
        return element

class InstrumentConfiguration(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._id = None
            self._components = []
            self._param_group_ref = None
            self._software_ref = None
            self._cv_params = []
            self._user_params = []
            return
            
        self._id = etree_element.get("id")
        self._components = []
        self._param_group_ref = None
        self._software_ref = None
        self._cv_params = []
        self._user_params = []
        
        for param in [child for child in etree_element if child.tag.endswith('cvParam')]:
            self._cv_params.append(CVParam(param))
        for param in [child for child in etree_element if child.tag.endswith('userParam')]:

            self._user_params.append(UserParam(param))
            
        param_group_ref = etree_element.find("referenceableParamGroupRef")
        if param_group_ref is not None:
            self._param_group_ref = param_group_ref.get("ref")
            
        software_ref = etree_element.find("softwareRef")
        if software_ref is not None:
            self._software_ref = software_ref.get("ref")
            
        component_list = etree_element.find("componentList")
        if component_list is not None:
            for component in component_list:
                self._components.append(Component(component))
    
    def add_component(self, component:Component):
        self._components.append(component)
        
    def set_param_group_ref(self, ref:str):
        self._param_group_ref = ref
        
    def set_software_ref(self, ref:str):
        self._software_ref = ref

    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
        
    @property
    def id(self):
        return self._id
    
    @property
    def components(self):
        return self._components
    
    @property
    def param_group_ref(self):
        return self._param_group_ref
    
    @property
    def software_ref(self):
        return self._software_ref
    
    @property
    def cv_params(self):
        return self._cv_params

    @property
    def user_params(self):
        return self._user_params
        
    def to_xml(self) -> etree._Element:
        element = etree.Element("instrumentConfiguration")
        element.set("id", self._id)

        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
        
        if self._param_group_ref is not None:
            param_group_ref = etree.SubElement(element, "referenceableParamGroupRef")
            param_group_ref.set("ref", self._param_group_ref)
            
        if self._software_ref is not None:
            software_ref = etree.SubElement(element, "softwareRef")
            software_ref.set("ref", self._software_ref)
            
        if len(self._components) > 0:
            component_list = etree.SubElement(element, "componentList")
            component_list.set("count", str(len(self._components)))
            for component in self._components:
                component_list.append(component.to_xml())
                
        return element

class ReferenceableParamGroup(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._id = None
            self._cv_params = []
            self._user_params = []
            return
            
        self._id = etree_element.get("id")
        self._cv_params = []
        self._user_params = []
        for param in etree_element.findall("cvParam"):
            self._cv_params.append(CVParam(param))
        for param in etree_element.findall("userParam"):
            self._user_params.append(UserParam(param))
    
    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
        
    @property
    def id(self):
        return self._id
    
    @property
    def cv_params(self):
        return self._cv_params

    @property
    def user_params(self):
        return self._user_params
        
    def to_xml(self) -> etree._Element:
        element = etree.Element("referenceableParamGroup")
        element.set("id", self._id)
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
        return element

class Sample(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._id = None
            self._name = None
            self._cv_params = []
            self._user_params = []
            return
            
        self._id = etree_element.get("id")
        self._name = etree_element.get("name")
        self._cv_params = []
        self._user_params = []
        for param in etree_element.findall("cvParam"):
            self._cv_params.append(CVParam(param))
        for param in etree_element.findall("userParam"):
            self._user_params.append(UserParam(param))
    
    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
        
    @property
    def id(self):
        return self._id
        
    @property
    def name(self):
        return self._name
    
    @property
    def cv_params(self):
        return self._cv_params

    @property
    def user_params(self):
        return self._user_params
        
    def to_xml(self) -> etree._Element:
        element = etree.Element("sample")
        if self._id is not None:
            element.set("id", self._id)
        if self._name is not None:
            element.set("name", self._name)
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
        return element

class Software(object):
    def __init__(self, etree_element: etree._Element = None):
        if etree_element is None:
            self._id = None
            self._version = None
            self._cv_params = []
            self._user_params = []
            return
            
        self._id = etree_element.get("id")
        self._version = etree_element.get("version")
        self._cv_params = []
        self._user_params = []
        for param in etree_element.findall("cvParam"):
            self._cv_params.append(CVParam(param))
        for param in etree_element.findall("userParam"):
            self._user_params.append(UserParam(param))
    
    def add_cv_param(self, cv_param:CVParam):
        self._cv_params.append(cv_param)

    def add_user_param(self, user_param:UserParam):
        self._user_params.append(user_param)
        
    @property
    def id(self):
        return self._id
    
    @property
    def version(self):
        return self._version
    
    @property
    def cv_params(self):
        return self._cv_params

    @property
    def user_params(self):
        return self._user_params
        
    def to_xml(self) -> etree._Element:
        element = etree.Element("software")
        element.set("id", self._id)
        element.set("version", self._version)
        for cv_param in self._cv_params:
            element.append(cv_param.to_xml())
        for user_param in self._user_params:
            element.append(user_param.to_xml())
        return element
