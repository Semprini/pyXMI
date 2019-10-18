#!/usr/bin/python
import sys
import os
import json
import yaml

from lxml import etree
from jinja2 import Template, Environment, FileSystemLoader

from xmi.uml.parse import ns, parse_uml, UMLPackage, UMLClass, UMLAttribute

settings = None

class InstanceValidationError(object):
    def __init__(self, case, error):
        self.case = case
        self.error = error
        
    def __repr__(self):
        return "Instance error: {}{} | {}".format(self.case.package.path, self.case.name, self.error)


class ClassValidationError(object):
    def __init__(self, package, cls, error):
        self.package = package
        self.error = error
        self.cls = cls
        
    def __repr__(self):
        return "Class error: {}{} | {}".format(self.package.path, self.cls.name, self.error)


class AttributeValidationError(object):
    def __init__(self, package, cls, attr, error):
        self.package = package
        self.error = error
        self.cls = cls
        self.attr = attr
        
    def __repr__(self):
        return "Attribute error: {}{}.{} | {}".format(self.package.path, self.cls.name, self.attr.name, self.error)


def validate_package(package,settings):
    errors = []
    
    for cls in package.classes:
        if not hasattr(cls,'domain'):
            errors.append( ClassValidationError(package,cls,"Class does not belong to a domain") )
    
        if cls.id_attribute == None and cls.is_abstract == False:
            if cls.supertype == None or cls.supertype.id_attribute == None:
                errors.append( ClassValidationError(package,cls,"no primary key") )
        elif cls.supertype != None:
            if cls.supertype.id_attribute != None and cls.id_attribute != cls.supertype.id_attribute:
                errors.append( ClassValidationError(package,cls,"To allow polymorphism the primary key must be defined in only the supertype") )

        has_id = False
        for attr in cls.attributes:
            if attr.stereotype == "auto" and attr.type != "int":
                errors.append( AttributeValidationError(package,cls,attr,"auto increment field must be int") )

            if attr.classification == None and attr.type not in settings['types'].keys():
                errors.append( AttributeValidationError(package,cls,attr,"unknown type: {}".format(attr.type)) )
                
            if attr.is_id == True:
                if has_id == True:
                    errors.append( AttributeValidationError(package,cls,attr,"multiple ID attributes detected") )
                has_id = True
                
            if attr.name == 'is_deleted':
                errors.append( AttributeValidationError(package,cls,attr,"is_deleted is a reserved attribute name") )
            
    for child in package.children:
        errors += validate_package(child,settings)
        
    return errors


def validate_test_cases(instance, settings):
    errors = []

    if instance.parent == None:
        if instance.stereotype != 'request':
            errors.append( InstanceValidationError(instance,"No classifier found for {}".format(instance.name)) )
    else:
        # Check all attributes against the classifier
        for attr in instance.attributes:
            valid_attr = False
            for cls_attr in instance.parent.attributes:
                if attr.name == cls_attr.name:
                    valid_attr = True
            if instance.parent.supertype != None:
                for cls_attr in instance.parent.supertype.attributes:
                    if attr.name == cls_attr.name:
                        valid_attr = True
            
            for cls_assoc in instance.parent.associations_from:
                if attr.name == cls_assoc.source_name:
                    valid_attr = True

            for cls_assoc in instance.parent.associations_to:
                if attr.name == cls_assoc.dest_name:
                    valid_attr = True
                    
            if not valid_attr:
                errors.append( InstanceValidationError(instance,"Incorrect attribute found in {}: {}".format(instance.name, attr.name)) )

        # Check associations against the classifier
        for assoc in instance.associations_to:
            valid_assoc = False
            for cls_assoc in instance.parent.associations_from:
                if assoc.source.parent in (cls_assoc.source,cls_assoc.source.supertype,cls_assoc.dest,cls_assoc.dest.supertype):
                    valid_assoc = True
            for cls_assoc in instance.parent.associations_to:
                if assoc.dest.parent in (cls_assoc.source,cls_assoc.source.supertype,cls_assoc.dest,cls_assoc.dest.supertype):
                    valid_assoc = True
                    
            if valid_assoc==False and instance.parent.supertype is not None:
                for cls_assoc in instance.parent.supertype.associations_from:
                    if assoc.source.parent in (cls_assoc.source,cls_assoc.source.supertype,cls_assoc.dest,cls_assoc.dest.supertype):
                        valid_assoc = True
                for cls_assoc in instance.parent.supertype.associations_to:
                    if assoc.dest.parent in (cls_assoc.source,cls_assoc.source.supertype,cls_assoc.dest,cls_assoc.dest.supertype):
                        valid_assoc = True
            
            if not valid_assoc:
                errors.append( InstanceValidationError(instance,"Incorrect association found from {}(id={}|type={}) to {}".format(instance.name, instance.id, instance.parent.name, assoc.dest_name)) )
                for cls_assoc in instance.parent.associations_from:
                    print("From {} | {} | {} | {}".format(instance.name, instance.parent.name, cls_assoc.dest_name, cls_assoc.source_name ))
                for cls_assoc in instance.parent.associations_to:
                    print("To {} | {} | {} | {}".format(instance.name, instance.parent.name, cls_assoc.dest_name, cls_assoc.source_name ))

        for assoc in instance.associations_from:
            valid_assoc = False
            for cls_assoc in instance.parent.associations_from:
                if assoc.source.parent in (cls_assoc.source,cls_assoc.source.supertype,cls_assoc.dest,cls_assoc.dest.supertype):
                    valid_assoc = True
            for cls_assoc in instance.parent.associations_to:
                if assoc.dest.parent in (cls_assoc.source,cls_assoc.source.supertype,cls_assoc.dest,cls_assoc.dest.supertype):
                    valid_assoc = True

            if valid_assoc==False and instance.parent.supertype is not None:
                for cls_assoc in instance.parent.supertype.associations_from:
                    if assoc.source.parent in (cls_assoc.source,cls_assoc.source.supertype,cls_assoc.dest,cls_assoc.dest.supertype):
                        valid_assoc = True
                for cls_assoc in instance.parent.supertype.associations_to:
                    if assoc.dest.parent in (cls_assoc.source,cls_assoc.source.supertype,cls_assoc.dest,cls_assoc.dest.supertype):
                        valid_assoc = True

            if not valid_assoc:
                errors.append( InstanceValidationError(instance,"Incorrect association found to {} from {}".format(assoc.dest_name, instance.name, )) )
                for cls_assoc in instance.parent.associations_from:
                    print("From {} | {} | {} | {}".format(instance.name, instance.parent.name, cls_assoc.dest_name, cls_assoc.source_name ))
                for cls_assoc in instance.parent.associations_to:
                    print("To {} | {} | {} | {}".format(instance.name, instance.parent.name, cls_assoc.dest_name, cls_assoc.source_name ))


        for assoc in instance.associations_from:
            errors += validate_test_cases(assoc.dest,settings)

    return errors


def validate(recipie_path):
    global settings
    
    config_filename = recipie_path+"/config.yaml"
    os.environ.setdefault("PYXMI_SETTINGS_MODULE", config_filename )

    with open(config_filename, 'r') as config_file:
        settings=yaml.load(config_file.read(), Loader=yaml.SafeLoader)

    tree = etree.parse(settings['source'])
    model=tree.find('uml:Model',ns)
    root_package=model.xpath("//packagedElement[@name='%s']"%settings['root_package'], namespaces=ns)
    if len(root_package) == 0:
        print("Root packaged element not found. Settings has:{}".format(settings['root_package']))
        return
    root_package=root_package[0]
    
    extension=tree.find('xmi:Extension',ns)

    model_package, test_cases = parse_uml(root_package, tree)
    
    # validations
    # Does each object have a primary key
    # Do objects with primary keys have a parent class which also has a primary key
    # Are all auto increment fields int
    print(validate_package(model_package,settings))
    
    # Does each class have a domain
    # Are there unexpected attribute types
    
    for case in test_cases:
        print(validate_test_cases(case,settings))
    