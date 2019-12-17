#!/usr/bin/env python
import os
import sys
import re
import time
import subprocess
import argparse
import tempfile

p = argparse.ArgumentParser()
p.add_argument('nth', type=int, help='nth')
p.add_argument('command', help='command')
p.add_argument('-F', '--delimiter', help='default: awk style')
p.add_argument('--p1')
p.add_argument('--p3')
args = p.parse_args()

if args.delimiter is not None and len(args.delimiter) > 1:
    print('[Error] Delimiter must be ONE character', file=sys.stderr)
    sys.exit(1)

try:

    def get_parts(line, pattern):
        if args.nth == 0:
            return ('', line, '')
        elif args.nth > 0:
            count = 0
            if args.delimiter is None:
                for m in re.finditer(pattern, line):
                    count += 1
                    if count >= args.nth:
                        left = line[:m.start()]
                        target = m.group(0)
                        right = line[m.end():]
                        return (left, target, right)
                return (line, '', '')
            else:
                start = 0
                for m in re.finditer(pattern, line + args.delimiter):
                    count += 1
                    if count >= args.nth:
                        left = line[:start]
                        target = line[start:m.start()-1]
                        right = line[m.end()-1:]
                        return (left, target, right)
                    start = m.end()
                return (line, '', '')
        elif args.nth < 0:
            matches = []
            if args.delimiter is None:
                for m in re.finditer(pattern, line):
                    matches.append(m)
                if len(matches) >= -args.nth:
                    m = matches[len(matches) + args.nth]
                    left = line[:m.start()]
                    target = m.group(0)
                    right = line[m.end():]
                    return (left, target, right)
                return ('', '', line)
            else:
                for m in re.finditer(pattern, line + args.delimiter):
                    matches.append(m)
                if len(matches) >= -args.nth:
                    end = 0
                    if len(matches) + args.nth - 1 >= 0:
                        end = matches[len(matches) + args.nth - 1].end()
                    m = matches[len(matches) + args.nth]
                    left = line[:end]
                    target = line[end:m.start()]
                    right = line[m.start():]
                    return (left, target, right)
                return ('', '', line)

    if len(args.command) > 0:
        sys.stdout.reconfigure(line_buffering=True)
        if args.delimiter is None:
            pattern = r'\S+'
        else:
            pattern = r'[{}]'.format(args.delimiter)
        with tempfile.TemporaryDirectory() as tmpdir:
            p1 = os.path.join(tmpdir, 'p1')
            p2 = os.path.join(tmpdir, 'p2')
            p3 = os.path.join(tmpdir, 'p3')
            os.mkfifo(p1)
            os.mkfifo(p2)
            os.mkfifo(p3)
            subprocess.Popen(
                "cat {} | {} | python {} 0 '' --p1 {} --p3 {}".format(
                    p2, args.command, __file__, p1, p3),
                shell=True,
                stdout=sys.stdout,
                text=True)
            with open(p1, 'w') as p1:
                with open(p2, 'w') as p2:
                    with open(p3, 'w') as p3:
                        line = sys.stdin.readline()
                        while line:
                            parts = get_parts(line.strip('\n'), pattern)
                            print(parts[0], file=p1)
                            print(parts[1], file=p2)
                            print(parts[2], file=p3)
                            line = sys.stdin.readline()
    elif args.p1 is not None and args.p3 is not None:
        with open(args.p1) as p1:
            with open(args.p3) as p3:
                line1 = p1.readline()
                line2 = sys.stdin.readline()
                line3 = p3.readline()
                while line1 and line2 and line3:
                    line1 = line1.strip('\n')
                    line2 = line2.strip('\n')
                    line3 = line3.strip('\n')
                    print('{}{}{}'.format(line1, line2, line3))
                    line1 = p1.readline()
                    line2 = sys.stdin.readline()
                    line3 = p3.readline()
except BrokenPipeError:
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
    sys.exit(1)
