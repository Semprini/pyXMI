# pyXMI

Parser and tools to manipulate XMI files (Sparx EA Generated)

Can be used to parse XMI file into classes which are passed to jinja2 templates for code generation. 

To generate code a recipie folder is provided:
> python generate.py <recipie path>

The recipie folder must have a config.json file which specifies templates and output.
