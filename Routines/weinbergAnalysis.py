import logging
import os
# import subprocess

from wolframclient.evaluation import WolframLanguageSession
from wolframclient.language import wlexpr  # wl,
from wolframclient.serializers import export


def getWeinbergAngle(dataDict, threadNumber='0'):
    '''
            Starts a Wolfram WolframLanguage Session and runs the code in /Documents/Wolfram Mathematica/pyMathTest.m
        with the parameters defined in dataDict.

        Arguments:
            - dataDict  :   Type(Dict) containing all the parameters necesary for the Weinberg analysis.

        Returns:
            - weinbergAngle :   Type(Float) value of the resulting angle

    '''
    weinbergAnalysisPath = os.path.expanduser('~') + '/Documents/Wolfram Mathematica/pyMathTest.m'

    # Export the data rules to the Mathematica association filetype
    dataDict_wl = export(dataDict, pandas_dataframe_head='association')
    dataRuleExpr = wlexpr(bytes('dataRule=', 'utf-8') + dataDict_wl)

    # set the root level to INFO
    # logFileName = 'Weinberg_Log-' + threadNumber + '.log'  # '/dev/null'
    logging.basicConfig(level=logging.ERROR)  # , filename=logFileName)

    session = WolframLanguageSession()

    try:

        #  Run the Mathematica Weinber Angle Code
        with open(weinbergAnalysisPath, 'r') as mathIn:
            strMath = mathIn.read()

        weinbergExpr = wlexpr(strMath)
        session.evaluate(dataRuleExpr)

        weinbergAngle = session.evaluate(weinbergExpr)
    finally:
        session.terminate()
        print('\nWeinberg Angle value: ', weinbergAngle, '  for Thread Nb-', threadNumber)

    # Should probably rm the log files

    return weinbergAngle
