#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#UXML: UXML structured metadata
"""

# -----------------------------------------------------------------------------
# :author:    Pete R. Jemian
# :email:     prjemian@gmail.com
# :copyright: (c) 2014-2020, Pete R. Jemian
#
# Distributed under the terms of the Creative Commons Attribution 4.0 International Public License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------


from lxml import etree
import os
import six

from .. import eznx
from ..plugin import AutoRegister
from ..plugin import ControlLineHandler
from ..utils import strip_first_word


DEFAULT_XML_ROOT_TAG = "UXML"
UXML_PROVIDES_ROOT_TAG = False
XML_SCHEMA = os.path.join(os.path.dirname(__file__), "uxml.xsd")


class UXML_Error(Exception):
    pass


@six.add_metaclass(AutoRegister)
class UXML_metadata(ControlLineHandler):

    """
    **#UXML** -- XML metadata in scan header

    IN-MEMORY REPRESENTATION

    * (SpecDataFileScan): **UXML** : XML document root

    HDF5/NeXus REPRESENTATION

    * various items below the *NXentry* parent group,
      as indicated in the UXML

    .. rubric:: Public methods

    .. autosummary::

          ~process

    .. rubric:: Internal methods

    .. autosummary::

          ~walk_xml_tree
          ~make_NeXus_links
          ~prune_dict
          ~dataset
          ~group
          ~hardlink

    """

    key = r"#UXML"
    scan_attributes_defined = ["UXML", "UXML_root"]
    unique_id = {}
    target_id = {}
    selector = None
    converters = dict(int=int, float=float, str=str)

    def process(self, text, scan, *args, **kws):
        """read #UXML lines from SPEC data file into ``scan.UXML``"""
        if not hasattr(scan, "UXML"):
            scan.UXML = []

        line = strip_first_word(text)
        scan.UXML.append(line)
        scan.addPostProcessor("UXML_metadata", self.postprocess)

    def postprocess(self, scan, *args, **kws):
        """
        convert the UXML text into an XML object (``scan.UXML_root``)

        :param SpecDataFileScan scan: data from a single SPEC scan
        """
        xml_text = "\n".join(scan.UXML)
        if UXML_PROVIDES_ROOT_TAG:
            root = etree.fromstring(xml_text)
            # read root_tag from supplied UXML lines
        else:
            # provide default root tag
            xml_text = (
                "<%s>\n" % DEFAULT_XML_ROOT_TAG
                + xml_text
                + "\n</%s>" % DEFAULT_XML_ROOT_TAG
            )
            root = etree.fromstring(xml_text)

        scan.UXML_root = root
        # validate against the schema
        xml_schema_tree = etree.parse(XML_SCHEMA)
        xml_schema = etree.XMLSchema(xml_schema_tree)

        if not xml_schema.validate(root):
            # XML file is not valid, let lxml report what is wrong as an exception
            # log = xmlschema.error_log    # access more details
            try:
                xml_schema.assertValid(root)  # basic exception report
            except etree.DocumentInvalid as exc:
                emsg = "UXML error: " + str(exc)
                # logger.warn(emsg)
                raise UXML_Error(emsg)

        scan.addH5writer("UXML_metadata", self.writer)

    def writer(self, nxentry, writer, scan, *args, **kws):
        """Describe how to store this data in an HDF5 NeXus file"""
        self.unique_id = {}
        self.target_id = {}
        self.selector = dict(
            dataset=self.dataset, group=self.group, hardlink=self.hardlink
        )

        # parse the XML and store
        self.walk_xml_tree(
            eznx.makeGroup(
                nxentry, "UXML", "NXnote", desc="UXML metadata"
            ),
            scan.UXML_root,
        )
        self.make_NeXus_links()

    def walk_xml_tree(self, h5parent, xml_node):
        """parse the XML node into HDF5 objects"""
        for item in xml_node:
            handler = self.selector[item.tag]
            handler(h5parent, item)

    def make_NeXus_links(self):
        """create all the hardlinks as directed"""
        for target_id in self.target_id.keys():
            if target_id in self.unique_id:
                target_group, target_name = self.target_id[target_id]
                source = self.unique_id[target_id]
                eznx.makeLink(target_group, source, target_name)

    def prune_dict(self, d, keys):
        """remove keys from dictionary d"""
        return {k: v for k, v in d.items() if k not in keys}

    def dataset(self, h5parent, xml_node):
        """HDF5/NeXus dataset specification"""
        attrs = dict(xml_node.attrib)
        nm = attrs.get("name")
        data_type = attrs.get("type", "str")
        unique_id = attrs.get("unique_id")
        attrs = self.prune_dict(attrs, "name type unique_id".split())

        if data_type in self.converters:
            converter = self.converters[data_type]
            value = converter(xml_node.text)
        else:
            emsg = "unexpected type='%s'" % data_type
            raise UXML_Error(emsg)

        ds = eznx.makeDataset(h5parent, nm, value, **attrs)

        if unique_id is not None:
            self.unique_id[unique_id] = ds

        return ds

    def group(self, h5parent, xml_node):
        """HDF5/NeXus group specification"""
        attrs = dict(xml_node.attrib)
        nm = attrs.get("name")
        NX_class = attrs.get("NX_class")
        unique_id = attrs.get("unique_id")
        attrs = self.prune_dict(attrs, "name NX_class unique_id".split())

        group = eznx.makeGroup(h5parent, nm, NX_class, **attrs)

        if unique_id is not None:
            self.unique_id[unique_id] = group

        self.walk_xml_tree(group, xml_node)

        return group

    def hardlink(self, h5parent, xml_node):
        """HDF5/NeXus hard link specification"""
        attrs = dict(xml_node.attrib)
        nm = attrs.get("name")
        target_id = attrs.get("target_id")

        if target_id is not None:
            self.target_id[target_id] = (h5parent, nm)
