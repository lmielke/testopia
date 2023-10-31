# logger.py
import os, re, time
import logging
from datetime import datetime as dt
# from . import settings as sts


def mk_logger(logDir, fileName, loggerName, *args, createLog=True, **kwargs):
    # logging config to put somewhere before calling functions
    # call like: logger.debug(f"logtext: {anyvar}")
    if not createLog: return None
    logger = logging.getLogger(loggerName)
    logger.setLevel(logging.INFO)
    logformat = "%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s"
    datefmt = "%m-%d %H:%M"
    logForm = logging.Formatter(fmt=logformat, datefmt=datefmt)
    logPath = os.path.join(logDir, fileName)
    logHandler = logging.FileHandler(logPath, mode="a")
    logHandler.setFormatter(logForm)
    logger.addHandler(logHandler)
    return logger

def manage_logs(logDir, *args, cleanup, logPreserveThreshold, **kwargs) -> None:
    """
    checks if number of logs or age of logs exceeds threshold
    NOTE: warnings will only be issued on verbose -v
    """
    check_log_dir(logDir, *args, **kwargs)
    if cleanup:
        remove_logs(logDir, logPreserveThreshold, *args, **kwargs)
    else:
        issue_warnings(logDir, logPreserveThreshold, *args, **kwargs)

def check_log_dir(logDir:str, *args, **kwargs) -> None:
    """
    checks if logDir exists, if not it creates it
    """
    if not os.path.exists(logDir):
        os.makedirs(logDir)

def issue_warnings(logDir:str, threshold:dict, *args, verbose, **kwargs) -> None:
    if verbose and threshold["count"] is not None:
        files = os.listdir(logDir)
        if len(files) > threshold["count"] * sts.warningTolerance:
            print(  f"WARNING: {len(files)} logfiles found in {logDir} !\n",
                    f" Use -c to cleanup !{color.Style.RESET_ALL}"
            )
    elif verbose and threshol["days"] is not None:
        fileAge = dt.now().day - dt.fromtimestamp(os.path.getctime(file)).day
        if fileAge > threshold["days"] * sts.warningTolerance:
            print(  f"WARNING: logfiles in {logDir} are older {threshold['days']} days !\n",
                    f" Use -c to cleanup !{color.Style.RESET_ALL}"
            )

def remove_logs(logDir:str, threshold:dict, *args, verbose, **kwargs) -> None:
    """
    Scans the logDir and removes all logfiles that excede the threshold
    as defined in logPreserveThreshold
    example: logPreserveThreshold = {"days": 30, "count": None}
    NOTE: This runs at the beginning of the test, so you will end up having more than what
    is defined by the threshold. This is because the logfiles are created during the test.
    NOTE: if sts.warningTolerance is set to value != 1 then warnings will always appear
    """
    for i, file in enumerate(sorted(os.listdir(logDir), reverse=False)):
        if verbose: print(f"file {i}: {file}")
        if file.endswith(".log"):
            file = os.path.join(logDir, file)
            if threshold["count"] is not None:
                if i > threshold["count"]:
                    if verbose: print(f"removing {file} because: {i} > {threshold['count']}")
                    os.remove(file)
            elif threshold["days"] is not None:
                fileAge = dt.now().day - dt.fromtimestamp(os.path.getctime(file)).day
                if fileAge > threshold["days"]:
                    time.sleep(1)
                    os.remove(file)