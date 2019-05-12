
class UMLPackage(object):
	def __init__(self, parent=None):
		self.classes = []
		self.children = []
		self.parent = parent

	def parse(self, element):
		self.name = element.get('name')
		#print(element.attrib)
		
		for child in element:	
			e_type = child.get('{http://www.omg.org/spec/XMI/20131001}type')

			if e_type == 'uml:Package':
				cls = UMLPackage(self)
				cls.parse(child)
				self.children.append( cls )
			
			elif e_type == 'uml:Class':
				cls = UMLClass(self)
				cls.parse(child)
				self.classes.append( cls )
					

class UMLClass(object):
	def __init__(self, parent):
		self.attributes = []
		self.parent = parent

	def parse(self, element):
		self.name = element.get('name')

		for child in element:	
			e_type = child.get('{http://www.omg.org/spec/XMI/20131001}type')

			if e_type == 'uml:Property':
				cls = UMLAttribute(self)
				cls.parse(child)
				self.attributes.append( cls )


class UMLAttribute(object):
	def __init__(self, parent=None):
		self.parent = parent

	def parse(self, element):
		self.name = element.get('name')
		
