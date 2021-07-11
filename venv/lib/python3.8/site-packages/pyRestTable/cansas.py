#!/usr/bin/env python

import io
import sys
from lxml import etree
try:
    # python 3
    from urllib.request import urlopen
except ImportError:
    # python 2
    from urllib2 import urlopen
sys.path.insert(0, '..')
from pyRestTable import Table

SVN_BASE_URL = 'http://www.cansas.org/svn/1dwg/trunk'
GITHUB_BASE_URL = 'https://raw.githubusercontent.com/canSAS-org/1dwg/master'
CANSAS_URL = '/'.join((GITHUB_BASE_URL, 'examples/cs_af1410.xml'))


def main():
    nsmap = dict(cs='urn:cansas1d:1.1')

    r = urlopen(CANSAS_URL).read().decode("utf-8")
    doc = etree.parse(io.StringIO(r))

    node_list = doc.xpath('//cs:SASentry', namespaces=nsmap)
    t = Table()
    t.labels = ['SASentry', 'description', 'measurements']
    for node in node_list:
        s_name, count = '', ''
        subnode = node.find('cs:Title', namespaces=nsmap)
        if subnode is not None:
            s = etree.tostring(subnode, method="text")
            s_name = node.attrib['name']
            count = len(node.xpath('cs:SASdata', namespaces=nsmap))
        title = s.strip().decode()
        t.rows += [[s_name, title, count]]

    return t


if __name__ == '__main__':
    table = main()
    # use "complex" since s_name might be empty string
    print(table.reST(fmt='complex'))
