import inspect
import rsMap3D.gui.input as rsmInput
from rsMap3D.gui.input.abstractfileview import AbstractFileView
import importlib

print (dir (input))
print("-------")
names = []
module = importlib.import_module(rsmInput.__name__)
print module
print("-------")
print inspect.getmembers(module, inspect.isclass)
print("-------")
for obj in inspect.getmembers(module, inspect.isclass):
    print obj
    if inspect.isclass(obj[1]) and issubclass( obj[1], AbstractFileView):
        
        names.append(obj[1].__module__ + "." + obj[1].__name__)
for name in names:
    print name