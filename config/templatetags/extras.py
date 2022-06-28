from django import template

register = template.Library()


@register.filter(name='zeroadd')
def zeroadd(value, arg):
    return str(value).zfill(arg)


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

