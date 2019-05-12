from lxml import etree
from jinja2 import Template

from uml import UMLPackage, UMLClass, UMLAttribute

ns={
	'uml':'http://www.omg.org/spec/UML/20131001',
	'xmi':'http://www.omg.org/spec/XMI/20131001',
	'umldi':'http://www.omg.org/spec/UML/20131001/UMLDI', 
	'dc':'http://www.omg.org/spec/UML/20131001/UMLDC',
}
	

def parse_packagedElement(element):
	e_type = element.get('{http://www.omg.org/spec/XMI/20131001}type')
	if e_type in classes.keys():
		cls = classes[e_type]()
		cls.parse(element)
		return cls
		

classes = {
	'uml:Package':UMLPackage,
}

tree = etree.parse("c:/temp/customer.xml")


model=tree.find('uml:Model',ns)
extension=tree.find('xmi:Extension',ns)

for child in model:
	if child.tag == 'packagedElement':
		package = parse_packagedElement(child)
		
		t = Template("Hello {{ package.name }}!")
		print(t.render(package=package))
