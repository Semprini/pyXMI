source = './test_recipie/test.xmi'

templates = [
    { 
        'source':'entities.jdl',
        'level':'package',
        'dest':'./build/test_output{{package.path}}{{package.name}}.jdl'
    }
]

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
