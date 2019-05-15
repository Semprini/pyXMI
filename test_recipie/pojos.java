package nz.co.genesis-energy.{{ package.parent.name }}.{{ package.name }};

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;

{% for child in package.classes %}@Entity
public class {{ child.name }}()
{
    {% for attr in child.attributes %}{% if attr.is_id %}
    @Id{% endif %}
    @Column (name = "{{attr.name}}"{% if attr.dest_type == 'String' %}, length={{attr.length}}{% endif %}){% if attr.association %}
    @Expandable (name = "{{attr.name}}", expandableClass = {{ attr.type }}.class){% endif %}
    private {{attr.dest_type}} {{attr.name}};
    {% endfor %}
    {% for attr in child.attributes %}
    public {{ attr.dest_type }} get{{ attr.name }}() {
        return {{ attr.name }};
    }

    public void set{{ attr.name }}({{ attr.dest_type }} {{ attr.name }}) {
        this.{{ attr.name }} = {{ attr.name }};
    }    
    {% endfor %}
}

{% endfor %}

