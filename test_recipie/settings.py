source = './test_recipie/test.xmi'

templates = [
    { 
        'source':'pojos.java',
        'dest':'c:/temp/{{package.name}}.java'
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
