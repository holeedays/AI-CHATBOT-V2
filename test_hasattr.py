
class MyObj:
    @property
    def my_prop(self):
        return 'value'

d = {'key': 'val'}
o = MyObj()

print(f"Object has property 'my_prop': {hasattr(o, 'my_prop')}")
print(f"Dict has key 'key' via hasattr: {hasattr(d, 'key')}")
print(f"Dict has method 'get' via hasattr: {hasattr(d, 'get')}")
