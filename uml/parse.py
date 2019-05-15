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
        
        if self.parent is None:
            self.root_package=self
        else:
            self.root_package=self.parent.root_package


    def parse(self, element, root):
        self.name = element.get('name')
        self.id = element.get('{%s}id'%ns['xmi'])

        if self.parent is None:
            self.path = '/' + self.root_package.name + '/'
        else:
            self.path = self.parent.path + self.name + '/'

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

        print("Parsed package with {} classes: {}{}".format( len(self.classes), self.path, self.name ) )
        

    def parse_associations(self):
        for cls in self.classes:
            cls.parse_associations(self.root_package)

        for child in self.children:
            child.parse_associations()


    def find_by_id(self, id):
        for cls in self.classes:
            if cls.id == id:
                return cls

        for child in self.children:
            return child.find_by_id(id)


class UMLClass(object):
    def __init__(self, package):
        self.attributes = []
        self.package = package


    def parse(self, element, root):
        self.name = element.get('name')
        self.id = element.get('{%s}id'%ns['xmi'])

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


    def parse_associations(self, root_package):
        for attr in self.attributes:
            if attr.association is not None:
                attr.destination = root_package.find_by_id(attr.destination_id)
                if attr.destination is not None:
                    attr.name = attr.destination.name.lower()
                    attr.type = attr.destination.name
                    for dest_attr in attr.destination.attributes:
                        if dest_attr.is_id:
                            attr.dest_type = dest_attr.dest_type
                            attr.length = dest_attr.length


class UMLAttribute(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.settings = importlib.import_module(os.environ.get('PYXMI_SETTINGS_MODULE'))
        self.association = None


    def parse(self, element, root):
        
        self.name = element.get('name')
        self.id = element.get('{%s}id'%ns['xmi'])
        
        #Detail is sparx sprecific
        #TODO: Put modelling tool in settings and use tool specific parser here
        detail = root.xpath("//attribute[@xmi:idref='%s']"%self.id, namespaces=ns)[0]
        properties = detail.find('properties')
        self.type = properties.get('type')
        if self.type[:4]=='enum':
            self.dest_type = 'enum'
        else:
            self.dest_type = self.settings.types[properties.get('type')]

        xrefs = detail.find('xrefs')
        if xrefs.get('value') is not None and 'NAME=isID' in xrefs.get('value'):
            self.is_id = True
        else:
            self.is_id = False
            
        #Todo: decide how to include string lengths in UML
        if self.type == 'string':
            self.length = 100


    def parse_association(self, element, root ):
        self.id = element.get('{%s}id'%ns['xmi'])
        self.association_id = element.get('association')
        dest_element = element.find('type')
        self.destination_id = dest_element.get('{%s}idref'%ns['xmi'])
        self.association = 'ManyToOne'
        