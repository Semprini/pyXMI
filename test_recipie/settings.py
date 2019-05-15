source = './test_recipie/test.xmi'

templates = [
    { 
        'source':'pojos.java',
        'level':'class',
        'dest':'c:/temp/{{cls.package.path}}/{{cls.name}}.java'
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
