# Testopia

## What is it
Testopia is a selection based <b>'python unittest'</b> launcher for <b>'Sublime Text 4'</b>. It is designed to directly test methods and functions from your 'Sublime Text' developing group using a single key press <b>Ctrl+b</b>. Testopia allows you to test your method/function or your entire module during development without having to leave 'Sublime Text', or even switching groups within Sublime.
Testopia assumes and supports a TDD (test driven) or TSD (test syncronous) development approach.


## How to use
Write your method or function within your python module.py file while syncronously writing your tests within your test_module.py file.
- leave your cursor within the function in any position other than the beginning of a line, press Ctrl+b to run the test for that individual method/function
- position your cursor at the begining of a line and press Ctrl+B to test the entire module
- use Sublimes multi cursor function to place your cursor in multiple functions/methods in order to test those methods/functions simultaneously
- select a region of your code and press Ctrl+B to test only methods/functions within that region
All test results will be displayed within the Sublime console.

## Installation and Setup
Before install check your Sublime and Project specification! (see Environment header below!)

- cd ~\AppData\Roaming\Sublime Text\Packages && git clone git@github.com:lmielke/testopia.git
- mv .\testopia.sublime-build ../User

- clone this repo into your Sublime Text 4 packages i.e. (~/AppData/Roaming/Sublime Text/Packages/) or download the zip file and unpack it into
- copy the testopia.sublime-build file into /Packages/User folder and adjust it to your needs
- make sure all variant parameters within the testopia.sublime-build file are set to your project specifications
- select testopia as build system for your project (Tools->Build System->testopia)

## Logging and Reporting
Testopia will create a test/testopia_logs/ folder within your test folder. This log folder will contain all test logs and will be updated with each test run. A new log file will be created each time you restart Sublime Text. You can limit the life time of your logfiles by adjusting the logPreserveThreshold within your testopia.sublime-build file. The default is set to 10, meaning that by default only the last 10 log files will be preserved.
Currently there is no Reporting implemented in Testopia. This is a feature that might be added in the future.


## Environment
- Sublime Text 4
- currently only Pipenv environments are supported
- requires a biased development setup with a test foder within your project directory 

## Issues
- in some cases the logfile from a previous test might not have been properly closed. In that case, save your work. Then close and reopen 'Sublime Text'. This will release the log. You can also increase the threshold for log preservation within the testopia.sublime-build file so it will not be deleted during
the current session.