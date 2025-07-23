"""
A Singleton pattern intended to be used as a counter, with the key a string and value a int or long.

This will be a meta-class in Python 2, but converts to true class in Python 3.
"""


def singleton(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance


@singleton
class TagCounter:

    def __init__(self):
        """ Constructor """
        self.count_map = {}

    def __repr__(self):
        """
        toString for python
        :return: string representing this object
        """
        keys = self.count_map.keys()
        keys.sort()
        to_string = 'TagCounter {\n'
        for key in keys:
            value = self.get_value(key)
            to_string += '{}: {}\n'.format(key, value)
        to_string += '}'

        return to_string

    def increment(self, key):
        """
        Check for this key if not found increment it.
        :param key:
        :return: None
        """
        value = self.get_value(key)
        if value > 0:
            self.count_map[key.lower()] = value + 1
        else:
            self.count_map[key.lower()] = 1

    def get_value(self, key):
        """ Return the value if in map, otherwise 0 if not."""
        return self.count_map.get(key.lower(), 0)

    def get_sorted_keys(self):
        """
        Get the sorted keys from the run.
        :return: list of keys
        """
        keys = self.count_map.keys()
        keys.sort()
        return keys

    def clear_counter(self):
        """
        Clear the counter after the run is finished.
        :return: None
        """
        self.count_map.clear()


def test_singleton():
    """
    Just for testing singleton.
    :return:
    """
    tg.increment('d')


# for testing
if __name__ == '__main__':
    tg = TagCounter()

    print (type(tg))

    tg.increment('a')
    tg.increment('b')
    tg.increment('a')

    a = tg.get_value('a')
    b = tg.get_value('b')
    c = tg.get_value('c')

    print('a={}, b={}, c={}'.format(a, b, c))

    test_singleton()
    test_singleton()
    test_singleton()
    test_singleton()

    d = tg.get_value('d')
    print('a={}, d={}'.format(a, d))

    print(tg)
