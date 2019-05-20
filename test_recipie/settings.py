# XMI source file
source = './test_recipie/test.xmi'

# List of outputs to generate
# level can either be package or class.
templates = [
    { 
        'source':'entities.jdl',
        'level':'package',
        'dest':'./build/test_output{{package.path}}{{package.name}}.jdl'
    },
    { 
        'source':'pojos.java',
        'level':'class',
        'dest':'./build/test_output{{cls.package.path}}{{cls.name}}.java'
    }
]

# UML to native translation of types.
types = {
    'string':'String',
    'decimal':'Double',
    'date':'Date',
    'dateTime':'DateTime',
    'long':'int',
    'boolean':'boolean',
    'integer':'int',
    'int':'int',
    'enum':'String',
}
