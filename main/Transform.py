import re
import Command
from Temporary import Temporary


class Transform():
    def __init__(self, transform, variables, delimiter):
        self.__command = ""
        self.__variables = variables
        self.__delimiter = delimiter
        self.set(transform)

    def is_empty(self):
        return len(self.__command) == 0

    def get_delimiter(self):
        return self.__delimiter

    def get_cmd(self):
        command = self.__variables.expand(self.__command)
        return command

    def set(self, transform):
        self.__command = transform

    def get_original_content(self, content):
        indexes = ','.join(
            list(
                map(lambda l: Command.awk_1(l, self.__delimiter),
                    content.split('\n'))))
        line_selector = self.__variables.expand(
            "{tooldir}/main/line_selector.pl")
        return Command.execute('cat {} | {} "{}"'.format(
            Temporary.temp_path('transform'), line_selector, indexes))

    def __adjust_visible(self, preview):
        for m in re.finditer(r'{visible:([^}]*)}', preview):
            preview = preview.replace(m.group(0), '{' + Transform.shift_index(m.group(1)) + '}')
        return preview

    def adjust_preview(self, preview):
        # {}           => 範囲指定なし
        # {..}         => range(1,-1)
        # {2}          => single(2)
        # {-2}         => single(-2)
        # {2..5}       => range(2,5)
        # {2..-2}      => range(2,-2)
        # {2..}        => range(2,-1)
        # {2..-2}      => range(2,-2)
        # {..5}        => range(1,5)
        # {..-2}       => range(1,-2)
        # comma separated is unsupported.
        # {1,3,5}      => [single(1),single(3),single(5)]
        # {1..3,2..5}  => [range(1,3),range(2,5)]

        base_cmd = 'cat {}'.format(Temporary.temp_path('transform'))
        base_cmd += ' | {tooldir}/main/line_selector.pl {index}'
        for m in re.finditer(r'{}', preview):
            preview = preview.replace(m.group(0), '$({})'.format(base_cmd))
        for m in re.finditer(r'{([-0-9]*)\.\.([-0-9]*)}', preview):
            start = m.group(1) if len(m.group(1)) > 0 else '1'
            end = m.group(2) if len(m.group(2)) > 0 else '-1'
            cmd = base_cmd + ' | {tooldir}/main/range.py '
            cmd += '{} {} {}'.format(
                '' if self.__delimiter is None else "-F '{}'".format(
                    self.__delimiter), start, end)
            preview = preview.replace(m.group(0), '$({})'.format(cmd))
        for m in re.finditer(r'{([-0-9]+)}', preview):
            cmd = base_cmd + ' | {tooldir}/main/single.py '
            cmd += '{} {}'.format(
                '' if self.__delimiter is None else "-F '{}'".format(
                    self.__delimiter), m.group(1))
            preview = preview.replace(m.group(0), '$({})'.format(cmd))
        preview = self.__adjust_visible(preview)
        preview = preview.replace('{index}', '{1}')
        return preview

    def shift_index(index):
        if len(index) == 0 or index == '..':
            return '2..'
        m = re.match(r'[1-9][0-9]*$', index)
        if m is not None:
            return str(int(index) + 1)
        m = re.match(r'(-?[1-9][0-9]*)\.\.(-?[1-9][0-9]*)', index)
        if m is not None:
            s = m.group(1)
            e = m.group(2)
            if len(s) > 0 and not s.startswith('-'):
                s = str(int(s) + 1)
            if len(e) > 0 and not e.startswith('-'):
                e = str(int(e) + 1)
            return '{}..{}'.format(s, e)
        return index

