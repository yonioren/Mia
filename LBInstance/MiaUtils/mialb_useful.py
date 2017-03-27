from os import popen
from socket import error as socket_error
from socket import inet_pton, AF_INET, gethostbyname


def get_ip(susppected_ip):
    try:
        inet_pton(AF_INET, susppected_ip)
    except socket_error:
        return gethostbyname(susppected_ip)
    return susppected_ip


def find_host_address():
    for line in popen("ip route show").readlines():
        l = line.split()
        if l[0] == 'default':
            return l[l.index('via') + 1]
    return False