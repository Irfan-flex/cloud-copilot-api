# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

class Map(dict):
    """
    Example:
    m = Map({'first_name': 'Eduardo'}, last_name='Pool', age=24, sports=['Soccer'])
    """

    def __init__(self, *args, **kwargs):
        """
        The `__init__` function initializes a `Map` object by populating it with key-value pairs from the
        arguments passed to the function.
        """
        super(Map, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.iteritems():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                self[k] = v

    def __getattr__(self, attr):
        """
        The `__getattr__` function is used to retrieve an attribute that does not exist in an object.
        """
        return self.get(attr)

    def __setattr__(self, key, value):
        """
        The `__setattr__` function is used to set an attribute value using the `__setitem__` method.

        """
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        """
        The `__setitem__` function updates the dictionary and adds the key-value pair to the object's
        attributes.
        """
        super(Map, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        """
        The `__delattr__` function is used to delete an attribute by calling the `__delitem__` function.
        """
        self.__delitem__(item)

    def __delitem__(self, key):
        """
        The `__delitem__` function is used to delete an item from a map object.
        """
        super(Map, self).__delitem__(key)
        del self.__dict__[key]
