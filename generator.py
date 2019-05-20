import os
import importlib

from lxml import etree
from jinja2 import Template, Environment, FileSystemLoader

from uml.parse import ns, UMLPackage, UMLClass, UMLAttribute

classes = {
    'uml:Package':UMLPackage,
}


def parse_packagedElement(element, tree):
    e_type = element.get('{%s}type'%ns['xmi'])
    if e_type in classes.keys():
        cls = classes[e_type]()
        cls.parse(element, tree)
        cls.parse_associations()
        return cls


def output(package):
    env = Environment(loader=FileSystemLoader(recipie_path))
    for template_definition in settings.templates:
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
        output(package)

