import os
import json

ns={
	'uml':'http://schema.omg.org/spec/UML/2.1',
	'xmi':'http://schema.omg.org/spec/XMI/2.1',
    'thecustomprofile':'http://www.sparxsystems.com/profiles/thecustomprofile/1.0',
    'NIEM_PSM_profile':'http://www.omg.org/spec/NIEM-UML/20130801/NIEM_PSM_Profile',
}

settings = None

def parse_uml(element, root):
    """ Root package parser entrypoint.
    """
    global settings
    
    with open(os.environ.get('PYXMI_SETTINGS_MODULE'), 'r') as config_file:
        settings=json.loads(config_file.read())

    e_type = element.get('{%s}type'%ns['xmi'])
    if e_type == 'uml:Package':
        package = UMLPackage()
        package.parse(element, root)
        package.parse_associations()
        return package
    else:
        print('Error - Non uml:Package element provided to packagedElement parser')



class UMLPackage(object):
    def __init__(self, parent=None):
        self.classes = []
        self.associations = []
        self.children = []
        self.parent = parent
        
        if self.parent is None:
            self.root_package=self
        else:
            self.root_package=self.parent.root_package


    def parse(self, element, root):
        """ Extract package details, call class parser for classes and self parser for sub-packages.
        Associations are not done here, but in a 2nd pass using the parse_associations function.
        """
        self.name = element.get('name')
        self.id = element.get('{%s}id'%ns['xmi'])
        self.element = element
        self.root_element = root

        # Package path is hierarchical. Add the current path onto it's parent
        if self.parent is None:
            self.path = '/' + self.root_package.name + '/'
        else:
            self.path = self.parent.path + self.name + '/'

        # Loop through all child elements and get classes and sub packages
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
        """ Packages and classes should already have been parsed so now we link classes for each association.
        This gets messy as XMI output varies based on association type. 
        This supports both un-specified and source to destination directional associations
        """
        for child in self.element:
            e_type = child.get('{%s}type'%ns['xmi'])
            e_id = child.get('{%s}id'%ns['xmi'])
            
            if e_type == 'uml:Association':
                assoc_source_id = None
                assoc_dest_id = None
                for assoc in child:
                    # If unspecified direction then both source and destination info are child elements within the association
                    assoc_type = assoc.get('{%s}type'%ns['xmi'])
                    assoc_id = assoc.get('{%s}id'%ns['xmi'])
                    if assoc_id is not None and assoc_type == 'uml:Property' and assoc_id[:8] == 'EAID_src':
                        assoc_source_elem = assoc
                        assoc_source_type_elem = assoc.find('type')
                        assoc_source_id = assoc_source_type_elem.get('{%s}idref'%ns['xmi'])
                    if assoc_id is not None and assoc_type == 'uml:Property' and assoc_id[:8] == 'EAID_dst':
                        assoc_dest_elem = assoc
                        assoc_dest_type_elem = assoc.find('type')
                        assoc_dest_id = assoc_dest_type_elem.get('{%s}idref'%ns['xmi'])
                
                # If association direction is source to destination then 
                # destination class info is found as an ownedAttribute in the source element
                if assoc_dest_id is None:
                    for assoc in child:
                        if assoc.tag == 'memberEnd':
                            assoc_idref = assoc.get('{%s}idref'%ns['xmi'])
                            if assoc_idref[:8] == 'EAID_dst':
                                assoc_dest_elem = self.root_element.xpath("//ownedAttribute[@xmi:id='%s']"%assoc_idref, namespaces=ns)[0]
                                assoc_dest_type_elem = assoc_dest_elem.find('type')
                                assoc_dest_id = assoc_dest_type_elem.get('{%s}idref'%ns['xmi'])
                
                # TODO: Raise error if we don't have a source and dest
                source = self.root_package.find_by_id(assoc_source_id)
                dest = self.root_package.find_by_id(assoc_dest_id)
                association = UMLAssociation(self, source, dest)
                association.parse(child, assoc_source_elem, assoc_dest_elem)
                self.associations.append(association)

        for child in self.children:
            child.parse_associations()


    def find_by_id(self, id):
        """ Finds and instantiated UMLClass object with specified Id
        Looks for classes part of this package and all sub-packages
        """
        for cls in self.classes:
            if cls.id == id:
                return cls

        for child in self.children:
            res = child.find_by_id(id)
            if res is not None:
                return res


class UMLAssociation(object):
    def __init__(self, package, source, dest):
        self.package = package
        self.source = source
        self.dest = dest
        source.associations_from.append(self)
        dest.associations_to.append(self)
        
    def parse(self, element, source_element, dest_element):
        self.source_name = self.dest.name.lower()
        self.dest_name = self.source.name.lower()
        
        source_lower = source_element.find('lowerValue').get('value')
        if source_lower == '-1':
            source_lower = '*'
        source_upper = source_element.find('upperValue').get('value')
        if source_upper == '-1':
            source_upper = '*'
        self.source_multiplicity = (source_lower, source_upper)

        dest_lower = dest_element.find('lowerValue').get('value')
        if dest_lower == '-1':
            dest_lower = '*'
        dest_upper = dest_element.find('upperValue').get('value')
        if dest_upper == '-1':
            dest_upper = '*'
        self.dest_multiplicity = (dest_lower, dest_upper)
        
        #print( '{}:{} to {}:{}'.format(self.source.name, self.source_multiplicity, self.dest.name, self.dest_multiplicity))
        
        if self.source_multiplicity[1] == '*' and self.dest_multiplicity[1] in ('0','1'):
            self.association_type = 'ManyToOne'
        elif self.dest_multiplicity[1] == '*' and self.source_multiplicity[1] in ('0','1'):
            self.association_type = 'OneToMany'
        elif self.dest_multiplicity[1] == '*' and self.source_multiplicity[1] == '*':
            self.association_type = 'ManyToMany'
        elif self.dest_multiplicity[1] in ('0','1') and self.source_multiplicity[1] in ('0','1'):
            self.association_type = 'OneToOne'

        if self.source_multiplicity[1] == '*':
            self.source_name += 's'
        if self.dest_multiplicity[1] == '*':
            self.dest_name += 's'
        #print('Assoc in {}: {} to {}: type = {}'.format(self.source.name, self.source_name, self.dest_name, self.association_type) )


class UMLClass(object):
    def __init__(self, package):
        self.attributes = []
        self.associations_from = []
        self.associations_to = []
        self.package = package


    def parse(self, element, root):
        self.name = element.get('name')
        self.id = element.get('{%s}id'%ns['xmi'])

        for child in element:    
            e_type = child.get('{%s}type'%ns['xmi'])

            if e_type == 'uml:Property':
                if child.get('association') is None and child.get('name') is not None:
                    cls = UMLAttribute(self)
                    cls.parse(child, root)
                    self.attributes.append( cls )


class UMLAttribute(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.association = None


    def parse(self, element, root):
        global settings
        
        self.name = element.get('name')
        self.id = element.get('{%s}id'%ns['xmi'])
        
        #Detail is sparx sprecific
        #TODO: Put modelling tool in settings and use tool specific parser here
        detail = root.xpath("//attribute[@xmi:idref='%s']"%self.id, namespaces=ns)[0]
        properties = detail.find('properties')
        self.type = properties.get('type')
        if self.type[:4]=='enum':
            self.dest_type = 'enum'
        elif properties.get('type') in settings['types'].keys():
            self.dest_type = settings['types'][properties.get('type')]
        else:
            self.dest_type = properties.get('type')
            
        xrefs = detail.find('xrefs')
        if xrefs.get('value') is not None and 'NAME=isID' in xrefs.get('value'):
            self.is_id = True
        else:
            self.is_id = False
            
        #Todo: decide how to include string lengths in UML
        if self.type == 'string':
            self.length = 100
        