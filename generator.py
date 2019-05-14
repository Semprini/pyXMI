import os
import importlib

from lxml import etree
from jinja2 import Template, Environment, FileSystemLoader

from uml.parse import ns, UMLPackage, UMLClass, UMLAttribute


def parse_packagedElement(element, tree):
    e_type = element.get('{%s}type'%ns['xmi'])
    if e_type in classes.keys():
        cls = classes[e_type]()
        cls.parse(element, tree)
        return cls


classes = {
    'uml:Package':UMLPackage,
}

recipie_path = 'test_recipie'

os.environ.setdefault("PYXMI_SETTINGS_MODULE", recipie_path+".settings")
settings = importlib.import_module(recipie_path+".settings")

tree = etree.parse(settings.source)
model=tree.find('uml:Model',ns)
extension=tree.find('xmi:Extension',ns)

for base in model:
    if base.tag == 'packagedElement':
        package = parse_packagedElement(base, tree)
        print("Base Package: "+package.name)

        for child in package.children:
            env = Environment(loader=FileSystemLoader(recipie_path))
            for template in settings.templates:
                t = env.get_template(template['source'])
                
                ft = Template(template['dest'])
                filename = ft.render(package=child)
                print("Writing: " + filename)
                with open(filename, 'w') as fh:
                    fh.write( t.render(package=child) )
