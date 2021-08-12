import pyRestTable


def main():
    t = pyRestTable.Table()
    t.addLabel('one')
    t.addLabel('two')
    t.addLabel('three')
    t.addRow( ['1,1', '1,2', '1,3',] )
    t.addRow( ['2,1', '2,2', '2,3',] )
    t.addRow( ['3,1', '3,2', '3,3',] )
    t.addRow( ['4,1', '4,2', '4,3',] )
    return t


if __name__ == '__main__':
    table = main()
    print(table.reST())
