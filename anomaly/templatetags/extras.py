from django import template

register = template.Library()


@register.filter(name='path')
def path(value, arg):
    str1 = str(value).split(arg)
    return str1[1]


@register.filter(name='phone')
def phone(value):
    phonenumber = ''
    inputnumber = str(value)

    phonenumber += inputnumber[0:3]
    phonenumber += '-'
    phonenumber += inputnumber[3:7]
    phonenumber += '-'
    phonenumber += inputnumber[7:]

    return phonenumber
