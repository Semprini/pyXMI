detail = root.xpath("//packagedElement[@xmi:id='%s']"%self.association_id, namespaces=ns)[0]
destination = root.xpath("//packagedElement[@xmi:id='%s']"%self.destination_id, namespaces=ns)[0]
self.name = destination.get('name').lower()
self.type = destination.get('name')

dest_detail_class = root.xpath("//element[@xmi:idref='%s']"%self.destination_id, namespaces=ns)[0]
dest_detail_attrs = dest_detail_class.find('attributes')
for attr in dest_detail_attrs:
   xrefs = attr.find('xrefs')
   if xrefs.get('value') is not None and 'NAME=isID' in xrefs.get('value'):
       properties = attr.find('properties')
       self.dest_type = self.settings.types[properties.get('type')]
       if properties.get('type') == 'string':
           self.length = 100
        