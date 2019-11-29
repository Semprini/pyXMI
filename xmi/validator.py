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


def validate_package(package, settings):
    errors = []

    for cls in package.classes:

        # Does each class have a domain
        if not hasattr(cls, 'domain'):
            errors.append(ClassValidationError(package, cls, "Class does not belong to a domain"))

        # Does each object have a primary key
        if cls.id_attribute is None and cls.is_abstract is False:
            if cls.supertype is None or cls.supertype.id_attribute is None:
                errors.append(ClassValidationError(package, cls, "no primary key"))

        elif cls.supertype is not None:
            # Do objects with primary keys have a parent class which also has a primary key
            if cls.supertype.id_attribute is not None and cls.id_attribute != cls.supertype.id_attribute:
                errors.append(ClassValidationError(package, cls,
                                                   "To allow polymorphism the primary key must be defined in only the supertype"))
            if 'auditable' in cls.stereotypes and 'auditable' not in cls.supertype.stereotypes:
                errors.append(ClassValidationError(package, cls,
                                                   "For inherited types to be auditable the supertype ({}) must also be auditable.".format(cls.supertype.name)))

        has_id = False
        for attr in cls.attributes:
            # Are all auto increment fields int or bigint
            if attr.stereotype == "auto" and attr.type not in ["int", "bigint"]:
                errors.append(
                    AttributeValidationError(package, cls, attr, "auto increment field must be int or bigint"))

            # Are there unexpected attribute types
            if attr.classification is None and attr.type not in settings['types'].keys():
                errors.append(AttributeValidationError(package, cls, attr, "unknown type: {}".format(attr.type)))

            # Check if there are multiple Id attributes
            if attr.is_id is True:
                if has_id is True:
                    errors.append(AttributeValidationError(package, cls, attr, "multiple ID attributes detected"))
                has_id = True

            # Check if there are attributes named using reserved keywords
            if attr.name == 'is_deleted':
                errors.append(AttributeValidationError(package, cls, attr, "is_deleted is a reserved attribute name"))

        if cls.is_supertype and package.domain != "Common":
            for cls_assoc in cls.associations_from:
                if package.domain != cls_assoc.dest.package.domain:
                    errors.append(ClassValidationError(package, cls,
                                                       "Supertypes must be in the 'Common' domain to have relations from objects ({}) in different domains").format(cls_assoc.dest.name))
            for cls_assoc in cls.associations_to:
                if package.domain != cls_assoc.source.package.domain:
                    errors.append(ClassValidationError(package, cls,
                                                       "Supertypes must be in the 'Common' domain to have relations to objects ({}) in different domains").format(cls_assoc.source.name))

    for child in package.children:
        errors += validate_package(child, settings)

    return errors


def validate_test_cases(instance, settings):
    errors = []

    if instance.parent == None:
        if instance.stereotype != 'request':
            errors.append(InstanceValidationError(instance, "No classifier found for {}".format(instance.name)))
    else:
        # Check all attributes against the classifier
        for attr in instance.attributes:
            valid_attr = False
            for cls_attr in instance.parent.attributes:
                if attr.name == cls_attr.name:
                    valid_attr = True
            if instance.parent.supertype is not None:
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
                errors.append(InstanceValidationError(instance, "Incorrect attribute found in {}: {}".format(instance.name, attr.name)))

        # Check associations against the classifier
        for assoc in instance.associations_to:
            valid_assoc = False
            for cls_assoc in instance.parent.associations_from:
                if assoc.source.parent in (cls_assoc.source, cls_assoc.source.supertype, cls_assoc.dest, cls_assoc.dest.supertype):
                    valid_assoc = True
            for cls_assoc in instance.parent.associations_to:
                if assoc.dest.parent in (cls_assoc.source, cls_assoc.source.supertype, cls_assoc.dest, cls_assoc.dest.supertype):
                    valid_assoc = True

            if valid_assoc == False and instance.parent.supertype is not None:
                for cls_assoc in instance.parent.supertype.associations_from:
                    if assoc.source.parent in (cls_assoc.source, cls_assoc.source.supertype, cls_assoc.dest, cls_assoc.dest.supertype):
                        valid_assoc = True
                for cls_assoc in instance.parent.supertype.associations_to:
                    if assoc.dest.parent in (cls_assoc.source, cls_assoc.source.supertype, cls_assoc.dest, cls_assoc.dest.supertype):
                        valid_assoc = True

            if not valid_assoc:
                errors.append(InstanceValidationError(instance,
                                                      "Incorrect association found from {}(id={}|type={}) to {}".format(
                                                          instance.name, instance.id, instance.parent.name,
                                                          assoc.dest_name)))

        for assoc in instance.associations_from:
            errors += validate_test_cases(assoc.dest, settings)

    return errors


def validate(recipie_path):
    global settings

    config_filename = recipie_path + "/config.yaml"
    os.environ.setdefault("PYXMI_SETTINGS_MODULE", config_filename)

    with open(config_filename, 'r') as config_file:
        settings = yaml.load(config_file.read(), Loader=yaml.SafeLoader)

    tree = etree.parse(settings['source'])
    model = tree.find('uml:Model', ns)
    root_package = model.xpath("//packagedElement[@name='%s']" % settings['root_package'], namespaces=ns)
    if len(root_package) == 0:
        print("Root packaged element not found. Settings has:{}".format(settings['root_package']))
        return
    root_package = root_package[0]

    extension = tree.find('xmi:Extension', ns)

    model_package, test_cases = parse_uml(root_package, tree)

    # validations
    print(validate_package(model_package, settings))

    for case in test_cases:
        print(validate_test_cases(case, settings))
