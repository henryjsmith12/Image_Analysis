#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

#-----------------------------------------------------------------------------
# :author:    Pete R. Jemian
# :email:     prjemian@gmail.com
# :copyright: (c) 2014-2020, Pete R. Jemian
#
# Distributed under the terms of the Creative Commons Attribution 4.0 International Public License.
#
# The full license is in the file LICENSE, distributed with this software.
#-----------------------------------------------------------------------------

"""
Format a nice table in reST (restructured text).

===========================  ============================================================
User Interface               Description
===========================  ============================================================
:class:`Table`               Construct a table in reST
:meth:`addLabel`             add label for one additional column
:meth:`addRow`               add list of items for one additional row
:meth:`setLongtable`         set `longtable` attribute
:meth:`setTabularColumns`    set `use_tabular_columns` & `alignment` attributes
:meth:`reST`                 render the table in reST format
===========================  ============================================================

.. autosummary::

    ~Table
    ~example_minimal
    ~example_basic
    ~example_complicated

"""


def _prepare_results_(t):
    s = [
        t.reST(fmt='plain'),
        t.reST(fmt='simple'),
        t.reST(fmt='grid'),
        t.reST(fmt='markdown'),
        t.reST(fmt='list-table'),
        t.reST(fmt='html')
    ]
    return "\n".join(s)


def example_minimal():
    """minimal example table"""
    t = Table()
    t.labels = ['x', 'y']
    t.addRow([1,2])
    return t


def example_basic():
    """basic example table"""
    t = Table()
    t.addLabel('one')
    t.addLabel('two')
    t.addLabel('three')
    t.addRow( ['1,1', '1,2', '1,3',] )
    t.addRow( ['2,1', '2,2', '2,3',] )
    t.addRow( ['3,1', '3,2', '3,3',] )
    t.addRow( ['4,1', '4,2', '4,3',] )
    return t


def example_complicated():
    """complicated example table"""
    t = Table()
    t.addLabel('Name\nand\nAttributes')
    t.addLabel('Type')
    t.addLabel('Units')
    t.addLabel('Description\n(and Occurrences)')
    t.addRow( ['one,\ntwo', "buckle my", "shoe.\n\n\nthree,\nfour", "..."] )
    t.addRow( ['class', 'NX_FLOAT', '', None, ] )
    t.addRow( range(0,4) )
    t.addRow( [None, {'a':1, 'b': 'dreamy'}, 1.234, list(range(3))] )
    t.setLongtable()
    t.setTabularColumns(True, 'l L c r'.split())
    return t


class Table(object):
    
    """
    Construct a table in reST (no row or column spans).
    
    :param bool use_tabular_columns: if True, embed table in
       Sphinx `'.. tabularcolumns:: |%s|' % alignment'` role
    :param [str] alignment: with `use_tabular_columns`, each 
       list item is a column format string, as specified by
       LaTeX *tabulary* package format:
       http://sphinx-doc.org/markup/misc.html?highlight=tabularcolumns#directive-tabularcolumns
    :param bool longtable: with `use_tabular_columns`, 
       if True, add Sphinx `:longtable:` directive

    MAIN METHODS

    .. autosummary::
    
        ~addLabel
        ~addRow
        ~reST

    SUPPORTING METHODS

    .. autosummary::
    
        ~setLongtable
        ~setTabularColumns
        ~plain_table
        ~simple_table
        ~grid_table
        ~list_table
        ~html_table

    """
    
    def __init__(self):
        self.rows = []
        self.labels = []
        self.use_tabular_columns = False
        self.alignment = []
        self.longtable = False
    
    def __str__(self):
        return self.reST()
    
    def addLabel(self, text):
        """
        add label for one additional column
        
        :param str text: column label text
        :return int: number of labels
        """
        self.labels.append(text)
        return len(self.labels)
    
    def addRow(self, list_of_items):
        """
        add list of items for one additional row
        
        :param [obj] list_of_items: list of items for one complete row
        :return int: number of rows
        """
        self.rows.append(list_of_items)
        return len(self.rows)
    
    def setLongtable(self, state = True):
        """
        set `longtable` attribute
        
        :param bool longtable: True | False
        """
        self.longtable = state
    
    def setTabularColumns(self, state=True, column_spec=None):
        """
        set `use_tabular_columns` & `alignment` attributes
        
        :param bool state: True | False
        :param [str] column_spec: list of column specifications
        """
        self.use_tabular_columns = state
        if state:
            self.alignment = column_spec or []

    def reST(self, indentation = '', fmt = 'simple'):
        """render the table in reST format"""
        if len(self.alignment) == 0:
            #  set the default column alignments
            self.alignment = str('L '*len(self.labels)).strip().split()
        if not len(self.labels) == len(self.alignment):
            msg = "Number of column labels is different from column width specifiers"
            raise IndexError(msg)
        xref = {
            'complex': self.grid_table,     # alias for `grid`, keep
            'grid': self.grid_table,
            'html': self.html_table,
            'list-table': self.list_table,
            'markdown' : self.markdown_table,
            'md' : self.markdown_table,     # alias for `markdown`, keep
            'plain': self.plain_table,
            'simple': self.simple_table,
            }
        if fmt not in xref:
            raise KeyError(
                f'format name "{fmt}" is unknown'
            )
        return xref[fmt](indentation)
    
    def plain_table(self, indentation = ''):
        """render the table in *plain* reST format"""
        # maximum column widths, considering possible line breaks in each cell
        width = self.find_widths()
        
        # build the row format strings
        fmt = " ".join(["%%-%ds" % w for w in width]) + '\n'
        
        rest = ''
        if self.use_tabular_columns:
            rest += indentation
            rest += '.. tabularcolumns:: |%s|' % '|'.join(self.alignment)
            if self.longtable:
                rest += '\n%s%s' % (' '*4, ':longtable:')
            rest += '\n\n'
        rest += self._row(self.labels, fmt, indentation) # labels
        for row in self.rows:
            rest += self._row(row, fmt, indentation)     # each row
        return rest
    
    def simple_table(self, indentation = ''):
        """render the table in *simple* reST format"""
        # maximum column widths, considering possible line breaks in each cell
        width = self.find_widths()
        
        # build the row separators
        separator = " ".join(['='*w for w in width]) + '\n'
        fmt = " ".join(["%%-%ds" % w for w in width]) + '\n'
        
        rest = ''
        if self.use_tabular_columns:
            rest += indentation
            rest += '.. tabularcolumns:: |%s|' % '|'.join(self.alignment)
            if self.longtable:
                rest += '\n%s%s' % (' '*4, ':longtable:')
            rest += '\n\n'
        rest += '%s%s' % (indentation, separator)        # top line of table
        rest += self._row(self.labels, fmt, indentation) # labels
        rest += '%s%s' % (indentation, separator)        # end of the labels
        for row in self.rows:
            rest += self._row(row, fmt, indentation)     # each row
        rest += '%s%s' % (indentation, separator)        # end of table
        return rest
    
    def grid_table(self, indentation = ''):
        """render the table in *grid* reST format"""
        # maximum column widths, considering possible line breaks in each cell
        width = self.find_widths()
        
        # build the row separators
        separator = '+' + "".join(['-'*(w+2) + '+' for w in width]) + '\n'
        label_sep = '+' + "".join(['='*(w+2) + '+' for w in width]) + '\n'
        fmt = '|' + "".join([" %%-%ds |" % w for w in width]) + '\n'
        
        rest = ''
        if self.use_tabular_columns:
            rest += indentation
            rest += '.. tabularcolumns:: |%s|' % '|'.join(self.alignment)
            if self.longtable:
                rest += '\n%s%s' % (' '*4, ':longtable:')
            rest += '\n\n'
        rest += '%s%s' % (indentation, separator)        # top line of table
        rest += self._row(self.labels, fmt, indentation) # labels
        rest += '%s%s' % (indentation, label_sep)         # end of the labels
        for row in self.rows:
            rest += self._row(row, fmt, indentation)     # each row
            rest += '%s%s' % (indentation, separator)    # row separator
        return rest
    
    def markdown_table(self, indentation = ''):
        """
        render the table in GitHub-flavored *markdown* (not reST) format
        
        see: https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet#tables
        """
        # build the row separators
        # maximum column widths, considering possible line breaks in each cell
        width = [max(w,3) for w in self.find_widths()]
        separator = "| " +" | ".join(['-'*w for w in width]) + ' |\n'
        fmt = "| " + " | ".join(["%%-%ds" % w for w in width]) + ' |\n'
        
        md = ''
        md += self._row(self.labels, fmt, indentation) # labels
        md += '%s%s' % (indentation, separator)        # end of the labels
        for row in self.rows:
            md += self._row(row, fmt, indentation)     # each row
        return md
    
    def list_table(self, indentation = ''):
        """
        render the table in *list-table* reST format:
        
        :see: http://docutils.sourceforge.net/docs/ref/rst/directives.html
        
        .. list-table:: Frozen Delights!
           :widths: 15 10 30
           :header-rows: 1
        
           * - Treat
             - Quantity
             - Description
           * - Albatross
             - 2.99
             - On a stick!
           * - Crunchy Frog
             - 1.49
             - If we took the bones out, it wouldn't be
               crunchy, now would it?
           * - Gannet Ripple
             - 1.99
             - On a stick!
        
        .. ... and, Yes, it _does_ work. 
        """
        
        def multiline(cell, prefix, indentation, fmt):
            r = []
            for i, line in enumerate(str(cell).splitlines()):
                if i > 0: s = ''
                else:     s = prefix
                r.append(indentation + fmt % s + line)
            return r
        
        widths = self.find_widths()
        rest  = [indentation + '.. list-table:: ', ]
        rest.append(indentation + '   :header-rows: 1')
        rest.append(indentation + '   :widths: ' + ' '.join(map(str, widths)))
        rest.append('')
        
        fmt = '%7s'
        
        rest += multiline(self.labels[0], '* - ', indentation, fmt)
        for cell in self.labels[1:]:
            rest += multiline(cell, '- ', indentation, fmt)
    
        for row in self.rows:
            rest += multiline(str(row[0]), '* - ', indentation, fmt)
            for cell in row[1:]:
                if cell is None or len(str(cell).strip()) == 0:
                    rest.append(indentation + fmt % '- ' + '')
                else:
                    rest += multiline(cell, '- ', indentation, fmt)
    
        return '\n'.join(rest)
    
    def html_table(self, indentation = ''):
        """render the table in *HTML*"""
        html = "<table>\n"
        html += '  <tr>\n'              # start the labels
        html += "".join(["    <th>{}</th>\n".format(k) for k in self.labels]) # labels
        html += '  </tr>\n'             # end the labels
        for row in self.rows:
            html += '  <tr>\n'          # start each row
            html += "".join(["    <td>{}</td>\n".format(k) for k in row]) # each row
            html += '  </tr>\n'         # end each row
        html += '</table>'              # end of table
        return html
    
    def _row(self, row, fmt, indentation = ''):
        """
        Given a list of entry nodes in this table row, 
        build one line of the table with one text from each entry element.
        The lines are separated by line breaks.
        """
        def pick_line(text, lineNum):
            """
            Pick the specific line of text or supply an empty string.
            Convenience routine when analyzing tables.
            """
            if lineNum < len(text):
                s = text[lineNum]
            else:
                s = ""
            return s
        text = ""
        if len(row) > 0:
            for line_num in range( max(map(len, [str(_).split("\n") for _ in row])) ):
                item = [pick_line(str(r).split("\n"), line_num) for r in row]
                text += indentation + fmt % tuple(item)
        return text
    
    def find_widths(self):
        """
        measure the maximum width of each column, 
        considering possible line breaks in each cell
        """
        
        def col_widths(columns):
            result = []
            for s in columns:
                # if multi-line, get width of biggest line
                widths = [len(p) for p in str(s).split("\n")]
                result.append(max(widths))
            return result
        
        width = []
        if len(self.labels) > 0:
            width = col_widths(self.labels)
        for row in self.rows:
            
            row_width = col_widths(row)
            
            if len(width) == 0:
                width = row_width
            width = list(map(max, zip(width, row_width) ))
        return width

