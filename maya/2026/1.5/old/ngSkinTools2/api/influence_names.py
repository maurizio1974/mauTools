import re

from ngSkinTools2.api.python_compatibility import Object
from ngSkinTools2.signal import Signal


class InfluenceNameFilter(Object):
    """
    simple helper object to match against filter strings;
    accepts filter as a string, breaks it down into lowercase tokens, and
    matches values in non-case sensitive way

    e.g. filter "leg arm spines" matches "leg", "left_leg",
    "R_arm", but does not match "spine"

    in a  special case of empty filter, returns true for isMatch
    """

    def __init__(self):
        self.matchers = []
        self.changed = Signal("filter changed")
        self.currentFilterString = ""

    def set_filter_string(self, filter_string):
        if self.currentFilterString == filter_string:
            # avoid emitting change events if there's no change
            return
        self.currentFilterString = filter_string

        def create_pattern(expression):
            expression = "".join([char for char in expression if char.lower() in "abcdefghijklmnopqrstuvwxyz0123456789_*"])
            expression = expression.replace("*", ".*")
            return re.compile(expression, re.I)

        self.matchers = [create_pattern(i.strip()) for i in filter_string.split() if i.strip() != '']
        self.changed.emit()
        return self

    def short_name(self, name):
        try:
            return name[name.rindex("|") + 1 :]
        except Exception as err:
            return name

    def is_match(self, value):
        if len(self.matchers) == 0:
            return True

        value = self.short_name(str(value).lower())
        for pattern in self.matchers:
            if pattern.search(value) is not None:
                return True

        return False


def short_name(name, min_len=0):
    """

    :param str name:
    :param int min_len:
    """
    idx = name.rfind("|", None, len(name) - min_len - 1)
    if idx < 0:
        return name
    return name[idx + 1 :]


class IndexedName(object):
    def __init__(self, path):
        self.path = path
        self.name = short_name(path)

    def extend_short_name(self):
        self.name = short_name(self.path, len(self.name))


def extend_unique_names(items, from_item):
    """

    :param int from_item:
    :param list[IndexedName] items:
    """

    if from_item >= len(items) - 1:
        return

    curr = items[from_item]
    needs_more_iterations = True
    while needs_more_iterations:
        needs_more_iterations = False
        curr_name = curr.name

        for item in items[from_item + 1 :]:
            if item.name == curr_name:
                if not needs_more_iterations:
                    curr.extend_short_name()
                item.extend_short_name()
                needs_more_iterations = True


def unique_names(name_list):
    """
    returns a list of shortened names without duplicates. e.g ["|a|b", "|a|b|c", "b|b"] will become ["a|b", "c", "b|b"]
    :param name_list:
    :return:
    """

    # assign index to each name to later restore the original order
    indexed_names = [IndexedName(i) for i in name_list]

    sorted_by_reveresed_name = sorted(indexed_names, key=lambda x: x.path[::-1])

    for i, _ in enumerate(sorted_by_reveresed_name):
        extend_unique_names(sorted_by_reveresed_name, i)

    return [i.name for i in indexed_names]
