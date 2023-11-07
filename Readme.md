# Testopia

## What is it
Testopia is a selection/cursor position based <b>'python unittest'</b> launcher for <b>'Sublime Text 4'</b>. It is designed to directly run python unittest from your 'Sublime Text' developing group using a single key press <b>Ctrl+b</b>. 

NOTE: This tool is in alpha. Quick start: https://www.youtube.com/watch?v=hmEVR6SLkt0
## How to use
While working on your class method within your python module.py file, syncronously work on your tests within your test/test_module.py file.

Then, to test:
1. place your cursor in <i>any position inside a method</i> (OTHER than the beginning of a line) and press <b>Ctrl+b</b> to run the test for that individual class/method
2. place your cursor at the <i>begining of a line</i> and press <b>Ctrl+b</b> to test the entire module
3. place your cursor <i>in multiple classes/methods</i> and press <b>Ctrl+b</b> to test those classes/methods simultaneously
4. <i>select a region</i> of your code and press <b>Ctrl+b</b> to test only classes/methods within that region
## Is it useful to you
Testopia assumes and facilitates a TDD (test driven) or TSD (test syncronous) continuous delivery approcach. It requires you to adhere to the folowing principles:

- Object oriented programming (<b>classes, methods</b>) in your <b>/package/module.py</b> file
- Object oriented Unitest(<b>unittest.TestCase</b>) setup using a <b>/test/test_module.py</b> file

Also Testopia is currently limited to some technical choices you make.

- Sublime Text 4 (test results will be displayed within the Sublime Console)
- <b>Pipienv</b> environments



## Installation and Setup
Before install check your Sublime and Project specification! (see Environment header below!)
### Environment
NOTE: This tool is in alpha, so do expect some bugs to show up! 
- Sublime Text 4
- currently only Pipenv environments are supported
- requires a biased development setup with a test foder within your project directory
### manual install
- clone this repo into your Sublime Text 4 packages or download the zip file and unpack it into the package folder
- this results in a directory like: <b>~/AppData/Roaming/Sublime Text/Packages/testopia</b>
- copy the <b>testopia.sublime-build</b> file into <b>/Packages/User</b> folder and adjust it to your needs
- make sure all variant parameters within the testopia.sublime-build file are set to your project specifications
- select testopia as a build system for your project (<b>Tools->Build System->testopia</b>)
### shell code snippet for Windows

```shell
    cd "~\AppData\Roaming\Sublime Text\Packages"
    git clone git@github.com:lmielke/testopia.git
    mv .\testopia\testopia.sublime-build ./User

    # in 'Sublime Text' select: Tools >> Build System >> testopia
```

## Logging and Reporting
Testopia will create a <b>test/testopia_logs/log...</b> folder within your test folder. This log folder will contain all test logs and will be updated with each test run. A new log file will be created each time you run the test <b>Ctrl+b</b>.

You can limit the life time of your logfiles by adjusting the <b>logPreserveThreshold</b> within your <b>testopia.sublime-build</b> file. The default is set to 10, meaning that by default only the last 10 log files will be preserved.
Currently there is no Reporting implemented in Testopia. This is a feature that might be added in the future.


## Issues
- in some cases the logfile from a previous test might not have been properly closed. In that case, save your work. Then close and reopen 'Sublime Text'. This will release the lock. You can also increase the threshold for log preservation within the testopia.sublime-build file so it will not be deleted during the current session.