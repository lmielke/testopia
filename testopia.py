import sublime
import sublime_plugin

import datetime as dt
from difflib import SequenceMatcher
import os, re, sys, time
import subprocess
from collections import defaultdict

# used to find all methods/functions in a file
funcRegex = r"(def\s+)([A-Za-z_0-9]*)(.*[)])(?:[ ->]*)(.*)(?=:\s*)"
classRegex = r'(?:^class\s*)([a-z_A-Z0-9]*)'

class Testopia:

    def __init__(self, vars, *args, **kwargs):
        self.kill = False
        self.vars = vars
        self.msg, self.missing, self.testMethods = [], set(), set()
        self.timeStamp = re.sub(r"([:. ])", r"-" , str(dt.datetime.now()))
        self.executable = TestExecutable(self.vars.get('folder'), *args, **kwargs)
        self.paths = FilePaths(self.msg, self.timeStamp, *args, **self.vars, **kwargs)

    def get_test_files(self, *args, **kwargs):
        with open(self.vars['file'], 'r') as f:
            self.moduleText = f.read()
        with open(self.paths.testFilePath, 'r') as f:
            self.testModuleText = f.read()
        self.classes = self.get_methods(self.moduleText, *args, **kwargs)

    def run_test(self, *args, verbose, **kwargs):
        self.get_test_files(*args, **kwargs)
        if verbose: print(f"\n\nNEXT Test: {self.vars}")
        # run the tests
        return self.executable.run_subprocess(
                                        self.vars.get('folder'),
                                        self.get_test_funcs(*args, verbose=verbose, **kwargs),
                                        self.paths,
                                        self.kill or self.paths.kill,
                                        *args,
                                        **kwargs
                )

    def get_methods(self, text, *args, defaultTestClassName, **kwargs):
        """
        returns a dictionary of classes and methods within the module file
        """
        methods, position, clName, testClName = dict(), 0, None, ''
        for line in text.split('\n'):
            if 'class ' in line or 'def ' in line:
                mMatch = re.search(funcRegex, line)
                if mMatch:
                    mName = mMatch.group(2)
                    funcStart = [p.start() for p in re.finditer(mName, line)][0] + position
                    methods[funcStart] = self.find_matching_test(
                                                                    clName,
                                                                    mName,
                                                                    testClName,
                                                                    *args, **kwargs
                                        )
                else:
                    clMatch = re.search(classRegex, line)
                    if clMatch:
                        clName = clMatch.group(1)
            position += (len(line) + 1)
        return methods

    def find_matching_test(self, clName, mName, testClName, *args,
                                testFuncPrefix, testClassPrefix, **kwargs):
        if self.paths.runFromPackageFile:
            if re.search(testClName, self.testModuleText) is None:
                self.missing.add(clName)
                testClName = None
                testMName = None
            else:
                testClName = f"{testClassPrefix}{clName}"
                testMName = f"{testFuncPrefix}{mName}"
        else:
            clName = clName.replace(testClassPrefix, '')
            mName = mName.replace(testFuncPrefix, '')
            testClName = f"{testClassPrefix}{clName}"
            testMName = f"{testFuncPrefix}{mName}"
        return clName, mName, testClName, testMName

    def check_dir_exists(self, dirName, *args, **kwargs):
        logDir = os.path.join(self.paths.testDir, dirName)
        if not os.path.isdir(logDir):
            os.mkdir(logDir)
        return logDir

    def get_test_funcs(self, log, level=0, *args, verbose, **kwargs):
        """
        finds the test functions within the test file and returns it
        if no test functions are found, the function finds the nearest definition above
        """
        testMethods = self.find_func_def(*args, **kwargs)
        # if no functions were found in selections, find the nearest function definition above
        if not testMethods and level == 0:
            self.find_nearest_func_def(*args, **kwargs)
            testMethods = self.find_func_def(level+1, *args, **kwargs)
        # testMethods = self.find_class_name(testMethods, *args, **kwargs)
        self.testMethods = {f"{self.classes[ix][2]}.{self.classes[ix][3]}" \
                                                                for func, ix in testMethods}
        if level == 0:
            log.info(
                    f"\n\ntestMethods: "
                    f"{self.testMethods if self.testMethods else 'all (no matches found)'}\n"
                    )
        if verbose: print(f"self.testMethods: {self.testMethods}")
        return self.testMethods

    def _find_cls_index(self, start, end, text, *args, testClassPrefix, testFilePrefix, 
                                                                                    **kwargs):
        mName = testFilePrefix + text.strip().split('(')[0].strip().split(' ')[-1]
        # find all indexes for 'def ' strings within self.moduleText
        ixs = [(m.start(), m.end()) for m in re.finditer(classRegex, self.moduleText)]
        # find the index of the last 'class ' string before the cursor position
        nearest = max([i[0] for i in ixs if i[0] < start])
        n = (nearest, nearest + ixs[1][1] - ixs[1][0])
        # select the entire line from self.moduleText that matches nearest index value
        testClName = (
                        f"{testClassPrefix}"
                        f"{self.moduleText[slice(n[0], n[1])].strip().split(' ')[-1]}"
                        )
        return testClName, mName



    def find_func_def(self, level=0, *args, defaultTestClassName, testFuncPrefix, **kwargs):
        """
            checks the .py file against the test_...py file and returns functions that 
            exist in both files
            NOTE: if the cursor is positioned at beginning of line, all functions are returned
                    which exist in both package.py and test_package.py files
            NOTE: if cursor is positioned inside a function, only this function is returned
        """
        testMethods = set()
        # find all functions within selections and add them to testMethods like test_found_func
        for i, sel in enumerate(self.vars['selectionTexts'].values()):
            selPos = self.moduleText.find(sel)
            for match in re.findall(funcRegex, sel):
                longMatch = ''.join(match[:2])
                mPos = [p.start() for p in re.finditer(longMatch, sel)][0] + len(match[0])
                m = ''.join(match[1])
                testMethods.add((m if m.startswith(testFuncPrefix) \
                                                else testFuncPrefix + m, mPos + selPos))
        return testMethods

    def find_nearest_func_def(self, *args, **kwargs):
        """
        Takes index tuples from selections and returns the nearest function definition
        located before the cursor position/selection position
        """
        for positions in self.vars['selectionTexts'].copy().keys():
            pos = positions[0]
            if self.moduleText[pos-1] == '\n':
                continue
            # find all indexes for 'def ' strings within self.moduleText
            ixs = [m.start() for m in re.finditer(f"{funcRegex[:-2]})", self.moduleText)]
            # find the index of the last 'def ' string before the cursor position
            nearest = max([i for i in ixs if i < pos])
            # select the entire line from self.moduleText that matches nearest index value
            n = (nearest, nearest + self.moduleText[nearest:].find('\n'))
            self.vars['selectionTexts'].update({n: self.moduleText[slice(n[0], n[1])]})





class FilePaths:

    def __init__(self, msg, *args, testFilePrefix, testDirName, ignoreDirs, **kwargs):
        self.kill = False
        self.msg = msg
        self.testFilePrefix = testFilePrefix
        self.runFromPackageFile = None
        self.ignoreDirs = set(ignoreDirs)
        self.similars = {}
        self.testDirName = testDirName
        self.mk_file_paths(*args, **kwargs)
        if not self.kill: self.mk_log_file_paths(*args, **kwargs)

    def mk_log_file_paths(self, timeStamp, *args, logDirName, **kwargs):
        self.logDir = os.path.join(self.testDir, logDirName)
        self.logName = f"{timeStamp}_{os.path.splitext(self.testFileName)[0]}.log"
        self.logPath = os.path.join(self.logDir, self.logName)

    def mk_file_paths(self, *args, file, file_path, **kwargs):
        """
        creates the paths for the test file depending on what was given to testopia
        if the test was run form test_something.py, than the test file is already known
        if the test was run from something.py, than the test_sumething.py file must be found
        """
        file_path = os.path.normpath(file_path).rstrip(os.sep)
        file = os.path.basename(file)
        # case1: test was run from test_something.py
        if file.startswith(self.testFilePrefix):
            self.runFromPackageFile = 0
            testFileDir = file_path
        # case2: test was run from something.py
        else:
            self.runFromPackageFile = 1
            testFileName = f"{self.testFilePrefix}{file}"
            testFileDir = self.find_test_dir(testFileName, file_path, *args, **kwargs)
        self._from_test_file(file, testFileDir, file_path, *args, **kwargs)

    def _from_test_file(self, file, testFileDir, *args, **kwargs):
        # if not os.path.isdir(testFileDir): return False
        self.testFileName = file if file.startswith(self.testFilePrefix) else \
                                                                self.testFilePrefix + file
        self.testDir = testFileDir
        self.testFilePath = os.path.join(testFileDir, self.testFileName)
        self.check_test_file(file, *args, **kwargs)

    def check_test_file(self, file, file_path, *args, **kwargs):
        if not os.path.isfile(self.testFilePath):
            self.msg.append(f"\nNot found {self.testFilePrefix}{file} in {file_path}")
            if self.similars:
                self.msg.append(f"Did you mean one of these: {self.similars}")
            self.kill = True
        return True

    def find_test_dir(self, file, file_path, *args, **kwargs):
        """
        takes a testFileName and a testDirName and finds the testFilePath
        it does so, by recursively searching for the sts.testDirName and 
        testFileName (i.e. test_something.py) starting from the package dir downwards
        """
        # find test folder starting from current dir
        foundDir = self.walklevels(os.path.basename(file), file_path, *args, **kwargs)
        if os.path.isdir(foundDir):
            return foundDir
        # try again from one level up
        self.ignoreDirs.add(os.path.basename(file_path))
        foundDir = self.walklevels(os.path.basename(file), file_path, *args, **kwargs)
        if os.path.isdir(foundDir):
            return foundDir
        return ''

    def walklevels(self, searchFile, searchPath, *args, numSearchLevels, **kwargs):
        num_sep = searchPath.count(os.sep)
        for root, dirs, files in os.walk(searchPath):
            num_sep_this = root.count(os.sep)
            # remove all entries from dirs which are in self.ignoreDirs
            for i, d in enumerate(dirs):
                if d in self.ignoreDirs:
                    del dirs[i]
            if searchFile in files:
                return root
            else:
                self.find_similars(searchFile, files, root, searchPath==root, *args, **kwargs)
            if num_sep + numSearchLevels <= num_sep_this:
                del dirs[:]
        return False

    def find_similars(self, searchFile, files, searchDir, ident, *args, **kwargs):
        """
        if no matching test file was found check for similar files due to spelling errors ect.
        """
        for file in files:
            if ident and file == searchFile.replace(self.testFilePrefix, '', 1): continue
            ratio = SequenceMatcher(None, os.path.basename(searchFile), file).ratio()
            if ratio >= 0.85:
                self.similars[file] = (os.path.basename(searchFile), searchDir, ratio)



class TestExecutable:

    def __init__(self, packageDir, *args, **kwargs):
        self.kill = False
        self.msg = []
        self.packageDir = packageDir
        self.projectName = os.path.basename(packageDir)
        self.path = self.get_exec_path(*args, **kwargs)
        self.source = 'python'

    def get_exec_path(self, *args, execsDir, **kwargs):
        """
            looks in various possible locations for the executable
            locations can be either the package directory itself or the ouside
            package Pipenv standard location
        """
        executables = []
        # first look inside the package directory
        venvFile = os.path.join(self.packageDir, '.venv')
        if os.path.exists(venvFile):
            with open(venvFile, 'r') as v:
                executable = v.read().strip()
                if os.path.exists(executable):
                    return executable.replace('/', os.sep)
        # if executable exists outside of package, get it from there
        execsDir = os.path.normpath(os.path.expanduser(execsDir))
        execs = [ex for ex in os.listdir(execsDir) if ex.startswith(self.projectName)]
        if self.check_executables(execs, execsDir, *args, **kwargs):
            return os.path.normpath(os.path.join(execsDir, execs[0], 'Scripts', 'python.exe'))
        return False

    def check_executables(self, execs, execsDir, *args, **kwargs):
        if len(execs) == 0:
            self.msg.append(f"No executalbe found for {self.projectName}")
            self.kill = True
        elif len(execs) == 1:
            return True
        elif len(execs) >= 2:
            self.msg.append(f"{self.projectName} test found mulitple envs {execs}")
            self.kill = True
        return False

    def run_subprocess(self, packageDir, testMethods, paths, kill, *args, **kwargs):
        """
        runs the test using subprocess.Popen
        """
        # run test cmds
        return (subprocess.Popen(
                    ['echo', 'Testopia ERROR:'] \
                                        if kill or self.kill \
                                        else [self.source, paths.testFilePath, *testMethods],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=packageDir,
                    executable=self.path,
                    ),
                    True)
