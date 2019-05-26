#!/usr/bin/python
import sys
import os
import json

from lxml import etree
from jinja2 import Template, Environment, FileSystemLoader

from uml.parse import ns, parse_uml, UMLPackage, UMLClass, UMLAttribute

settings = None


def output(package):
    env = Environment(loader=FileSystemLoader(recipie_path))
    for template_definition in settings['templates']:
        template = env.get_template(template_definition['source'])
        filename_template = Template(template_definition['dest'])
        
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
                filename = os.path.abspath(filename_template.render(cls=cls))
                dirname = os.path.dirname(filename)
                if not os.path.exists(dirname):
                    os.makedirs(dirname)
                print("Writing: " + filename)
                with open(filename, 'w') as fh:
                    fh.write( template.render(cls=cls) )

    for child in package.children:
        output(child)


def parse(recipie_path):
    global settings
    
    config_filename = recipie_path+"/config.json"
    os.environ.setdefault("PYXMI_SETTINGS_MODULE", config_filename )

    with open(config_filename, 'r') as config_file:
        settings=json.loads(config_file.read())

    tree = etree.parse(settings['source'])
    model=tree.find('uml:Model',ns)
    models=model.xpath("//packagedElement[@name='%s']"%settings['model_package'], namespaces=ns)
    if len(models) == 0:
        print("Root packaged element not found. Settings has:{}".format(settings['model_package']))
        return
    model=models[0]
    
    extension=tree.find('xmi:Extension',ns)

    package = parse_uml(model, tree)
    print("Base Package: "+package.name)
    output(package)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        recipie_path = 'test_recipie'
    else:
        recipie_path = str(sys.argv[1])

    parse(recipie_path)
    