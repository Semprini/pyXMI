{% for entity in package.classes %}

CREATE TABLE {{ entity.name }} ( {% for attr in entity.attributes[:-1] %}
  {{attr.name}} {{attr.dest_type}}{% if attr.is_id %}PRIMARY KEY{% endif %},{% endfor %}
);

{% endfor %}
