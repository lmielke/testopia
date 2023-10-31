import sublime
import sublime_plugin

import threading
import os, re, sys, time

from . import testopia
from . import logger



class UnitTestBuildCommand(sublime_plugin.WindowCommand):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.killed = False
        self.proc = None
        self.panel = None
        self.outMsg = ''
        self.panel_lock = threading.Lock()

    def is_enabled(self, *args, kill=False, **kwargs):
        # The Cancel build option should only be available
        # when the process is still running
        if kill:
            return self.proc is not None and self.proc.poll() is None
        return True


    def run(self, *args, kill=False, **kwargs):
        """
        main function that is called when the build system is run
        runs the tests an displays the results
        """
        if kill:
            if self.proc:
                self.killed = True
                self.proc.terminate()
            return
        self.prep_testing(*args, **kwargs)
        self.prep_logging(*args, **kwargs)
        # A lock is used to ensure only one thread is
        # touching the output panel at a time
        with self.panel_lock:
            # Creating the panel implicitly clears any previous contents
            self.panel = self.window.create_output_panel('exec')
            settings = self.panel.settings()
            settings.set('result_file_regex', r'^File "([^"]+)" line (\d+) col (\d+)')
            settings.set('result_line_regex', r'^\s+line (\d+) col (\d+)')
            settings.set('result_base_dir', self.vars.get('folder'))
            self.window.run_command('show_panel', {'panel': 'output.exec'})
        if self.proc is not None:
            self.proc.terminate()
            self.proc = None
        # test is run here and results are prepared for output
        self.proc, self.kill = self.test.run_test(self.log, *args, **kwargs)
        threading.Thread(target=self.read_handle, args=(self.proc.stdout, ) ).start()

    def prep_testing(self, *args, **kwargs):
        self.vars = self.get_vars()
        self.test = testopia.Testopia(self.vars, *args, **kwargs)

    def prep_logging(self, *args, **kwargs):
        if hasattr(self.test.paths, 'logDir'):
            logger.manage_logs(self.test.paths.logDir, *args, **kwargs)
            self.log = logger.mk_logger(
                                        self.test.paths.logDir,
                                        self.test.paths.logName,
                                        __name__,
                                        *args, **kwargs,
                        )
            # log will always contain self.vars as specified in testopia.sublime-build file
            self.log.info('\n' + '\n'.join([f"var {k}:\t{v}" for k, v in self.vars.items()]))

    def read_handle(self, handle):
        chunk_size = 2 ** 13
        out = b''
        while True:
            try:
                data = os.read(handle.fileno(), chunk_size)
                # If exactly the requested number of bytes was
                # read, there may be more data, and the current
                # data may contain part of a multibyte char
                out += data
                if len(data) == chunk_size:
                    continue
                if data == b'' and out == b'':
                    raise IOError('EOF')
                # We pass out to a function to ensure the
                # timeout gets the value of out right now,
                # rather than a future (mutated) version
                self.queue_write(out.decode('utf-8'))
                if data == b'':
                    raise IOError('EOF')
                out = b''
            except (UnicodeDecodeError) as e:
                msg = 'Error decoding output using %s - %s'
                self.queue_write(msg  % ('utf-8', str(e)))
                break
            except (IOError) as e:
                if self.killed:
                    msg = 'Cancelled'
                else:
                    msg = 'Finished'
                self.queue_write('\n[%s]' % msg)
                BuildScollTopCommand(self.window).run()
                break

    def queue_write(self, text):
        sublime.set_timeout(lambda: self.do_write(text), 1)
        try:
            self.log.info(text)
        except:
            # if no logger exists, then causing error messages are added to output
            msg = '\n'.join(self.test.msg) + '\n'.join(self.test.executable.msg)
            sublime.set_timeout(lambda: self.do_write(msg), 1)

    def do_write(self, text):
        with self.panel_lock:
            self.panel.run_command('append', {'characters': text})

    def get_vars(self, *args, **kwargs):
        vars = self.window.extract_variables()
        view = self.window.active_view()
        vars['selectionTexts'] = {tuple(t): view.substr(t) for t in view.sel()}
        return vars



class BuildScollTopCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.find_output_panel("exec")
        if not v:
            return
        v.run_command("move_to", {"to": "bof"})



def unalias_path(path: str) -> str:
    path = path.replace(r"%USERPROFILE%", "~")
    path = path.replace("~", os.path.expanduser("~"))
    if path.startswith("."):
        path = os.path.join(os.getcwd(), path[2:]).replace("/", os.sep)
    return path