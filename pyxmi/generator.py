#!/usr/bin/python
import sys
import os
import json

from lxml import etree
from jinja2 import Template, Environment, FileSystemLoader

from pyxmi.uml.parse import ns, parse_uml, UMLPackage, UMLClass, UMLAttribute

settings = None


def output_model(package, recipie_path):
    env = Environment(loader=FileSystemLoader(recipie_path))
    for template_definition in settings['templates']:
        template = env.get_template(template_definition['source'])
        filename_template = Template(template_definition['dest'])
        filter_template = None
        if 'filter' in template_definition.keys():
            filter_template = Template(template_definition['filter'])
        
        if template_definition['level'] == 'package':
            filename = os.path.abspath(filename_template.render(package=package))
            dirname = os.path.dirname(filename)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            print("Writing: " + filename)
            with open(filename, 'w') as fh:
                fh.write( template.render(package=package) )
        
        elif template_definition['level'] == 'class':
            for cls in package.classes:
            
                if filter_template is None or filter_template.render(cls=cls)=="True":
                    filename = os.path.abspath(filename_template.render(cls=cls))
                    dirname = os.path.dirname(filename)
                    if not os.path.exists(dirname):
                        os.makedirs(dirname)
                    print("Writing: " + filename)
                    with open(filename, 'w') as fh:
                        fh.write( template.render(cls=cls) )

    for child in package.children:
        output_model(child, recipie_path)


def output_test_cases(test_cases):
    for case in test_cases:
        serialised = json.dumps(serialize_instance(case), indent=2)
        
        for template_definition in settings['test_templates']:
            filename_template = Template(template_definition['dest'])
            filename = os.path.abspath(filename_template.render(ins=case))
            dirname = os.path.dirname(filename)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            print("Writing: " + filename)
            with open(filename, 'w') as fh:
                fh.write( serialised )


def serialize_instance(instance):
    ret = {}

    for attr in instance.attributes:
        ret[attr.name] = attr.value
    
    #for assoc in instance.associations_to:
    #    if assoc.source_multiplicity[1] == '*':
    #        if assoc.source.name not in ret.keys():
    #            ret[assoc.source.name] = [serialize_instance(assoc.source),]
    #        else:
    #            ret[assoc.source.name].append(serialize_instance(assoc.source))
    #    else:
    #            ret[assoc.source.name] = serialize_instance(assoc.source)

    for assoc in instance.associations_from:
        if assoc.dest_multiplicity[1] == '*':
            if assoc.dest.name not in ret.keys():
                ret[assoc.dest.name] = [serialize_instance(assoc.dest),]
            else:
                ret[assoc.dest.name].append(serialize_instance(assoc.dest))
        else:
                ret[assoc.dest.name] = serialize_instance(assoc.dest)
        
    return ret


def parse(recipie_path):
    global settings
    
    config_filename = recipie_path+"/config.json"
    os.environ.setdefault("PYXMI_SETTINGS_MODULE", config_filename )

    with open(config_filename, 'r') as config_file:
        settings=json.loads(config_file.read())

    tree = etree.parse(settings['source'])
    model=tree.find('uml:Model',ns)
    root_package=model.xpath("//packagedElement[@name='%s']"%settings['root_package'], namespaces=ns)
    if len(root_package) == 0:
        print("Root packaged element not found. Settings has:{}".format(settings['root_package']))
        return
    root_package=root_package[0]
    
    extension=tree.find('xmi:Extension',ns)

    model_package, test_cases = parse_uml(root_package, tree)
    print("Base Model Package: "+model_package.name)
    output_model(model_package, recipie_path)
    output_test_cases(test_cases)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        recipie_path = 'test_recipie'
    else:
        recipie_path = str(sys.argv[1])

    parse(recipie_path)
    