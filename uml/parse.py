import os
import importlib

ns={
	'uml':'http://schema.omg.org/spec/UML/2.1',
	'xmi':'http://schema.omg.org/spec/XMI/2.1',
    'thecustomprofile':'http://www.sparxsystems.com/profiles/thecustomprofile/1.0',
    'NIEM_PSM_profile':'http://www.omg.org/spec/NIEM-UML/20130801/NIEM_PSM_Profile',
}

    
class UMLPackage(object):
    def __init__(self, parent=None):
        self.classes = []
        self.children = []
        self.parent = parent

    def parse(self, element, root):
        self.name = element.get('name')

        for child in element:
            e_type = child.get('{%s}type'%ns['xmi'])
            
            if e_type == 'uml:Package':
                cls = UMLPackage(self)
                cls.parse(child, root)
                self.children.append( cls )

            elif e_type == 'uml:Class':
                cls = UMLClass(self)
                cls.parse(child, root)
                if cls.name is not None:
                    self.classes.append( cls )


class UMLClass(object):
    def __init__(self, parent):
        self.attributes = []
        self.parent = parent

    def parse(self, element, root):
        self.name = element.get('name')

        for child in element:    
            e_type = child.get('{%s}type'%ns['xmi'])

            if e_type == 'uml:Property':
                if child.get('association') is not None:
                    cls = UMLAttribute(self)
                    cls.parse_association(child, root)
                    self.attributes.append( cls )
                elif child.get('name') is not None:
                    cls = UMLAttribute(self)
                    cls.parse(child, root)
                    self.attributes.append( cls )


class UMLAttribute(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.settings = importlib.import_module(os.environ.get('PYXMI_SETTINGS_MODULE'))

    def parse(self, element, root):
        
        self.name = element.get('name')
        self.id = element.get('{%s}id'%ns['xmi'])
        
        detail = root.xpath("//attribute[@xmi:idref='%s']"%self.id, namespaces=ns)[0]
        properties = detail.find('properties')
        self.type = properties.get('type')
        if self.type[:4]=='enum':
            self.dest_type = 'enum'
        else:
            self.dest_type = self.settings.types[properties.get('type')]

        if self.type == 'string':
            self.length = 100
            
        xrefs = detail.find('xrefs')
        if xrefs.get('value') is not None and 'NAME=isID' in xrefs.get('value'):
            self.is_id = True
        else:
            self.is_id = False
            

    def parse_association(self, element, root ):
        self.id = element.get('{%s}id'%ns['xmi'])
        self.association_id = element.get('association')
        dest_element = element.find('type')
        self.destination_id = dest_element.get('{%s}idref'%ns['xmi'])
        
        detail = root.xpath("//packagedElement[@xmi:id='%s']"%self.association_id, namespaces=ns)[0]
        destination = root.xpath("//packagedElement[@xmi:id='%s']"%self.destination_id, namespaces=ns)[0]
        self.name = destination.get('name').lower()
        self.type = destination.get('name')
        self.association = 'ManyToOne'

        dest_detail_class = root.xpath("//element[@xmi:idref='%s']"%self.destination_id, namespaces=ns)[0]
        dest_detail_attrs = dest_detail_class.find('attributes')
        for attr in dest_detail_attrs:
            xrefs = attr.find('xrefs')
            if xrefs.get('value') is not None and 'NAME=isID' in xrefs.get('value'):
                properties = attr.find('properties')
                self.dest_type = self.settings.types[properties.get('type')]
                if properties.get('type') == 'string':
                    self.length = 100
                