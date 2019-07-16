'''
    Has algorithms for days
'''
from time import gmtime, strftime
import time
import numpy as np
import random
from random import randint
import json

from pprint import pprint as pp

from Utils.constrEval  import *
from Utils.printUtils import *
from Utils.SmartRandomGenerator.smartRand import *


def makeRegistrar():
    registry = {}
    def registrar(func):
        registry[func.__name__] = func
        return func  # normally a decorator returns a wrapped function,
                      # but here we return func unmodified, after registering it
    registrar.all = registry
    return registrar
regAlg = makeRegistrar()


def formatTopChi2List_asGen0( topChi2List, sortedChiSquare_ListOfTuples ):##### DOCUEMNTEATIN
    '''
    '''
    pointTree = {}

    for pointNb, pointDict in enumerate(topChi2List):

        pointKey = list(pointDict.keys())[0]
        newKey = 'G0-P' + str(pointNb)

        pointTree[newKey] = {}
        # pp(pointDict[pointKey])
        auxDict = { pointKey: { auxKey: pointDict[pointKey][auxKey] for auxKey in pointDict[pointKey].keys() }}



        # pp(pointDict[pointKey])
        # pp(auxDict)

        # pp(pointTree[newKey]['FullDescription'])
        pointTree[newKey] = pointDict[pointKey]
        pointTree[newKey]['Chi2'] = sortedChiSquare_ListOfTuples[pointNb][1]
        pointTree[newKey]['Parent'] = None
        pointTree[newKey]['Children'] = []

        pointTree[newKey]['FullDescription'] =  auxDict
        # pp(pointTree[newKey])

        # pp(pointTree[newKey])
        # pp(pointTree[newKey])
        # pointTree[newKey]['OrigKey'] = pointKey

    return pointTree
def makeBranch( pointDict, newChi2 , parentID, pointID ):
    '''
        E.g.   add Generation-2
    '''
    pointKey = list( pointDict.keys() ) [0]
    pointBranch = {}
    pointBranch[pointID] = {}

    pointBranch[pointID] .update( pointDict[pointKey] )
    pointBranch[pointID] .update( {'Chi2' : newChi2})
    pointBranch[pointID] .update( {'Children' : [] } )
    pointBranch[pointID] .update( {'Parent' : parentID } )
    pointBranch[pointID] .update( {'FullDescription' : pointDict } )

    # pp (pointBranch)


    return pointBranch

class minimAlg:
    '''
    '''
    def __init__(self, psObject, q, bestChiSquares, sortedChiSquare_ListOfTuples,  threadNumber = '0', minimisationConstr='Global', timeOut = 120, ignoreConstrList = [], noOfSigmasB = 1, noOfSigmasPM = 1, debug= False,  chi2LowerBound = 1.0):
        '''
        '''
        self.psObject = psObject


        self.modelConstr =  constrEval( self.psObject )
        self.generatingEngine = psObject.engineClass( self.psObject )

        self.Que = q
        self.bestChiSquares = bestChiSquares
        self.sortedChiSquare_ListOfTuples = sortedChiSquare_ListOfTuples
        self.threadNumber = threadNumber
        self.minimisationConstr = minimisationConstr
        self.timeOut = timeOut
        self.ignoreConstrList = ignoreConstrList
        self.noOfSigmasB = noOfSigmasB
        self.noOfSigmasPM = noOfSigmasPM
        self.debug = debug
        self.chi2LowerBound = chi2LowerBound

        return None

    @regAlg
    def diffEvol( self ):
        '''
            Differential evolution algorithm works as per Storn and Price [see ref]
        '''

        modelConstr = constrEval( self.psObject )
        pointTree =  formatTopChi2List_asGen0( self.bestChiSquares, self.sortedChiSquare_ListOfTuples )


        alphaParents = list (  pointTree.keys() )
        scanIDwThread = self.psObject.modelName + self.psObject.case.replace(" ","") + strftime("-%d-%m-%Y_%H_%M_%S", gmtime()) + '_ThreadNb' + self.threadNumber
        resultsDirDicts = self.psObject.resultDir + 'Dicts/Focus' + strftime("_%d_%m_%Y/", gmtime())

        # print(delimitator)
        resultDict_Thread = {}


        # chi2Min = sortedChiSquare_ListOfTuples[0][1]
        # pp(sortedChiSquare_ListOfTuples[0])
        # 'chi2Min': min( newListOfChi2 ),
        # 'chi2Mean' : np.mean( newListOfChi2),
        # 'chi2Std' : np.std( newListOfChi2)
        chi2Vals = [chi2Tuple[1] for chi2Tuple in self.sortedChiSquare_ListOfTuples ]
        listOfChi2StatDicts = [ { 'chi2Min': min(chi2Vals),
                'chi2Mean': np.mean(chi2Vals) ,
                'chi2Std': np.std(chi2Vals)
                             } ]


        listOfBestChi2 = [  sorted(self.sortedChiSquare_ListOfTuples, key=lambda tup: tup[1])[0][1]  ]
        ####  Pick target vector at rndom / as lowestchi2? ####
        # F_factor = 0.4
        # CR_factor = 0.1

        F_factor = 0.5
        CR_factor = 0.1
        generatingEngine = self.psObject.engineClass( self.psObject )



        #### Initialisation stage ####
        # Pick out 4 points in phase space and assign one of them as the target.

        ### This population size multiplier seems slightly unnecessary
        genPopSize = len(alphaParents)
        genNb = 0
        changeNb = 0


        while True:

            newParents = []
            pointCount = 0

            #### Populating the new generation. Stop when we have the same number of parents in the new one.
            while len(newParents) < genPopSize:

                for targetKey in alphaParents:



                    # alphaParentsMod = deepcopy(alphaParents)
                    # alphaParentsMod = [ parent for parent in alphaParents if parent != targetKey]
                    rndKeyChoice = random.sample(alphaParents , 3)

                    # targetKey = rndKeyChoice[0]
                    targetChi2 = pointTree[targetKey]['Chi2']




                    #### Mutation stage ####
                    # Create a donnor vector out of the parameters of the 3 others via the formula below.
                    donorDict = {}
                    for modelParam in self.psObject.params.keys():
                        xr1_Comp = pointTree[rndKeyChoice[0]][modelParam]
                        xr2_Comp = pointTree[rndKeyChoice[1]][modelParam]
                        xr3_Comp = pointTree[rndKeyChoice[2]][modelParam]

                        # F_factor = random.uniform(0, 2)

                        donorDict[modelParam] = xr1_Comp + F_factor * (xr2_Comp - xr3_Comp)

                    # alphaParents = [parentPoint for parentPoint in alphaParents if parentPoint not in rndKeyChoice]



                    #### Recombination stage ####
                    # Make a new hybrid vector

                    mutatedDict = {}
                    rndParamChoice = random.choice(list(  self.psObject.params.keys() ) )

                    for modelParam in self.psObject.params.keys():

                        if   random.uniform(0, 1) <= CR_factor or modelParam == rndParamChoice :
                            # print ('_________--------\\\\\\\\')
                            mutatedDict[modelParam] = donorDict[modelParam]
                        else:
                            # print('---------------------')
                            mutatedDict[modelParam] = pointTree[targetKey][modelParam]




                    ########### Selection stage ############

                    genValidPointOutDict = generatingEngine.runPoint( mutatedDict, threadNumber = self.threadNumber , debug = self.debug)
                    newPointWithAttr_int = generatingEngine._getRequiredAttributes(mutatedDict, self.threadNumber)
                    newPointWithAttr = self.psObject._getCalcAttribForDict( newPointWithAttr_int )
                    massTruth = generatingEngine._check0Mass( newPointWithAttr )



                    if  massTruth == True:

                        newPointKey = list(newPointWithAttr.keys())[0]

                        newChiSquared = modelConstr.getChi2(
                        newPointWithAttr[newPointKey], ignoreConstrList = self.ignoreConstrList, minimisationConstr = self.minimisationConstr, returnDict = False)
                    else:
                        newChiSquared = targetChi2 + 1


                    # newPointWithAttr = generatingEngine._getRequiredAttributes(mutatedDict, threadNumber)
                    ### New point evaluation

                    # print(newChiSquared, targetChi2)
                    # time.sleep(0.3)

                    if newChiSquared < targetChi2:

                        oldID = list(newPointWithAttr.keys())[0]
                        pointGenID = oldID + '-GenNb'+ str(genNb)

                        toAddDict = {}
                        toAddDict[pointGenID] = newPointWithAttr[oldID]
                        toAddChi2 = newChiSquared

                        # print(toAddChi2, list(toAddDict.keys()) )
                        with open( resultsDirDicts +'ScanResults.' + scanIDwThread + '.json', 'a') as outfile:
                            json.dump(toAddDict, outfile)

                    else:
                        toAddDict = pointTree[targetKey]['FullDescription']
                        toAddChi2 = targetChi2

                    generatingEngine._clean( self.threadNumber )
                    # print( delimitator )
                    ### Add to the new generation
                    pointCount += 1

                    # newPointKey = list(newPointDict['NewPointDict'].keys())[0]
                    # newParamsDict = newPointDict['NewPointDict']
                    # newChi2 = newPointDict['ChiSquared']

                    parentID = targetKey
                    childID = 'G' + str(genNb + 1) + '-P' + str(pointCount)
                    pointTree.update ( makeBranch( toAddDict, toAddChi2, parentID, childID) )

                    pointTree[parentID]['Children'].append( childID )
                    newParents.append( childID )

                    # resultDict_Thread.update( toAddDict )



                    # q.put( toAddDict )

            #### Move on to the new generation ####
            # print(len(newParents))
            alphaParents = newParents
            genNb += 1


            ##### Getting the smallest Chi2 and sending it to the plotting function ####
            chi2Min = pointTree[alphaParents[0]]['Chi2']
            # minKey = alphaParents[0]

            newListOfChi2 = []
            for  newParent in alphaParents:
                newListOfChi2.append(pointTree[newParent]['Chi2'])


            chi2Min, chi2Mean , chi2Std=  min( newListOfChi2 ), np.mean( newListOfChi2), np.std( newListOfChi2)
            # chi2Mean = np.mean( newListOfChi2)

            newChi2Dict = {
            'chi2Min': chi2Min,
            'chi2Mean' : chi2Mean,
            'chi2Std' : chi2Std,
            'chi2List' : newListOfChi2 }

                #
                # if pointTree[newParent]['Chi2'] < chi2Min:
                #     chi2Min = pointTree[newParent]['Chi2']
                #     minKey = newParent

            # pp(pointTree[minKey])
            ############# Printing section ###########
            quePut = False

            if chi2Min < listOfBestChi2[-1]:
                printStr = 'Minimum Decrease of'
                percChange = round ( (chi2Min - listOfBestChi2[-1]) / listOfBestChi2[-1], 4) * 100
                quePut = True

                changeNb += 1

                printGenMsg(genNb, chi2Min, self.threadNumber, printStr, percChange)

                # print(delimitator2)
                # print ('\n'+'For ' +Fore.GREEN+'Gen# ' + str(genNb)+ Style.RESET_ALL +
                #         ' the best' + Fore.RED +  ' χ² of ', round(chi2Min,4) ,
                #         Fore.YELLOW + ' from ThreadNb :' + str(int(threadNumber)+1) ,
                #          # ' from point ', minKey ,
                #         "   |   ", Fore.BLUE + printStr +  Style.RESET_ALL, percChange , '%' )
                # print(delimitator2)
            # elif chi2Min >  listOfBestChi2[-1]:
            #     printStr = 'Increase of'

            elif chi2Mean < listOfChi2StatDicts[-1]['chi2Mean']:
                printStr = 'Distribution Mean Decrease of'
                percChange = round ( (chi2Mean - listOfChi2StatDicts[-1]['chi2Mean']) /
                                    listOfChi2StatDicts[-1]['chi2Mean'], 4) * 100

                quePut = True
                changeNb += 1
                printGenMsg(genNb, chi2Min, self.threadNumber, printStr, percChange)


            if quePut ==  True:
                self.Que.put( {'GenNb': genNb,
                        'ThreadNb': int(self.threadNumber)+1,
                        'NewChi2': chi2Min,
                        'OldChi2': listOfBestChi2[-1],
                        'NewChi2Dict': newChi2Dict ,
                        'OldChi2Dict': listOfChi2StatDicts[-1] ,
                        'ChangeNb': changeNb
                        }
                    )
                with open(resultsDirDicts + 'GenStatus_ThreadNb'+ self.threadNumber +'.dat', 'a') as outFile:

                    outFile.write(  ''.join(  attrName + str(attr)+'   ||  '
                                            for attrName, attr in zip(['GenNb-', 'MinChi2: ', 'MeanChi2: ', 'StdChi2: '],
                                                                      [genNb, chi2Min, chi2Mean, chi2Std])
                                                        ) +'\n'  )

            # print(delimitator2)
            # print ('\n'+'For ' +Fore.GREEN+'Gen# ' + str(genNb)+ Style.RESET_ALL +
            #         ' the best' + Fore.RED +  ' χ² of ', round(chi2Min,4) ,
            #         Fore.YELLOW + ' from ThreadNb :' + str(int(threadNumber)+1) ,
            #          # ' from point ', minKey ,
            #         "   |   ", Fore.BLUE + printStr +  Style.RESET_ALL, percChange , '%' )
            # print(delimitator2)

            # chi2MinDict.update( {'GenNb-'+str(genNb) : {'BestChi2': chi2Min, 'rSigmaVal': best_rSigma}  } )
            # pp(chi2MinDict)

            # listOfBestChi2.append( newChi2Dict )
            listOfChi2StatDicts.append( newChi2Dict )
            listOfBestChi2.append(chi2Min)

            del listOfBestChi2[0]
            del listOfChi2StatDicts[0]

            if chi2Min < self.chi2LowerBound:

                print(Fore.RED + delimitator + Style.RESET_ALL)
                printCentered('Hit χ² bound of '+str(self.chi2LowerBound) +   '   :::   Killing Thread #' + str(int(self.threadNumber)+1), color=Fore.RED)
                print(Fore.RED + delimitator + Style.RESET_ALL)

                # print(Fore.YELLOW + delimitator + Style.RESET_ALL)
                self.Que.put( int(self.threadNumber)+1 )
                break



        return None


    def _lookAroundPointForSmallerChi2 (self, phaseSpacePointDict, startTime, best_rSigma):
        '''
            Given a point via phaseSpacePointDict, the function performs a random search in the hypercube defined by phaseSpacePointDict['Params'][param] ± sigmasDict[param] untill it finds a new point with a χ^2 smaller than the initial point. Requires a startTime to be externally monitored for timeOuts (recursive function calls itself).

            Arguments:
                - phaseSpacePointDict         ::      Dictionary of a point with the usual attributes: {'Params':{...}, 'Particles':{...}, 'Couplings': {...}}.
                - startTime                   ::      Time at which function is called (required outside).
                - threadNumber                ::      DEFAULT: '0'. Identifies process number.
                - minimisationConstr          ::      DEFAULT: 'Global' . By default function will find the global χ^2. Can be set to a list of a subset of constraints to find the combined χ^2.
                - timeOut                     ::      DEFAULT: 120. If after timeOut secconds the function hasn't found a new point with a smaller χ^2 then the function times out and returns None
                - noOfSigmasB                 ::       DEFAULT: 1 . Change this to relax number of sigmas for bounded params.
                - noOfSigmasPM                ::       DEFAULT: 1 . Change this to relax number of sigmas for parameter match.

            Return:
                - [newPointWithAttr, newPointConstraintDict, {'ChiSquared':newChiSquared}]    ::: IF IT HASN'T TIMED OUT.
                - None                                                                        ::: IF IT HAS TIMED OUT.

                A list with the newPoint with the required attributes, the new Point with attributes and constraints and the ChiSquared of the new point
        '''

        colorDict = {'0':Fore.RED, '1':Fore.GREEN, '2':Fore.YELLOW,  '3': Fore.BLUE , '4':Fore.MAGENTA}
        nbOfColors = len( list(colorDict.keys()) )

        generatingEngine = self.psObject.engineClass( self.psObject )
        smartRndGen = smartRand({}, self.psObject.condDict, self.psObject.rndDict, self.psObject.toSetDict)
        modelConstr = constrEval( self.psObject )


        ## TimeOut control
        if time.time() - startTime > self.timeOut:
            if debug:
                print (colorDict[ str(int(self.threadNumber) % nbOfColors) ] +
                        '-------------> ⏰ Timeout for thread Nb ' + self.threadNumber +' ⏰ <-------------' +
                        Style.RESET_ALL )

            return None


        pointKey = list(phaseSpacePointDict.keys())[0]
        # print(pointKey)
        # print(phaseSpacePointDict)
        chiSquareToMinimise = self.modelConstr.getChi2(phaseSpacePointDict[pointKey], ignoreConstrList = self.ignoreConstrList,
                                                        minimisationConstr = self.minimisationConstr, returnDict = False)

        # ### Ill defined original point
        # if chiSquareToMinimise == None:
        #     return None

        if self.debug:
            print(Fore.GREEN +'Χ^2 to  beat:  ' +  str(chiSquareToMinimise) + Style.RESET_ALL +' with ' + str(self.noOfSigmasB) + ' ,  ' +str(self.noOfSigmasPM) +  'σs \n')

        ### New point generation
        # generatingEngine = self.engineClass(self.modelName, self.case)

        while True:

            try:


                paramsDict = { modelAttr :phaseSpacePointDict[pointKey][modelAttr]   for modelAttr in self.psObject.params}
                newParamsDict = smartRndGen.genRandUniform_Rn( paramsDict , best_rSigma)
                ### Generate a point and extract its attributes

                # newParamsDict = generatingEngine._genPointAroundSeed(phaseSpacePointDict[pointKey]['Params'], best_rSigma, threadNumber = threadNumber, debug = debug)
                # newPointWithAttr = generatingEngine._getRequiredAttributes(newParamsDict, threadNumber)
                # massTruth = generatingEngine._check0Mass( newPointWithAttr )


                genValidPointOutDict = generatingEngine.runPoint( newParamsDict, threadNumber = self.threadNumber , debug = self.debug)
                newPointWithAttr_int = generatingEngine._getRequiredAttributes(newParamsDict, self.threadNumber)
                newPointWithAttr = self.psObject._getCalcAttribForDict(newPointWithAttr_int )
                massTruth = generatingEngine._check0Mass( newPointWithAttr )

                if  massTruth == False:
                    ### Point has 0 masses clean and try again.
                    generatingEngine._clean( self.threadNumber)
                    continue
                else:

                    ### Escape condition when massTruth = True, move on to next stage.
                    generatingEngine._clean( self.threadNumber)
                    break

            except Exception as e:
                raise
                print(e)


                ### Ill defined point clean and try again.
                generatingEngine._clean( self.threadNumber)
                continue


        ### New point evaluation
        newPointKey = list(newPointWithAttr.keys())[0]
        newChiSquared = self.modelConstr.getChi2(newPointWithAttr[newPointKey], ignoreConstrList = self.ignoreConstrList,
                                    minimisationConstr = self.minimisationConstr, returnDict = False)

        # #### Returns none in case the new ChiSquared isn't defined.
        # if newChiSquared == None:
        #     return None

        if self.debug:
            if newChiSquared > chiSquareToMinimise:

                print(Fore.RED +'New Χ^2 of ' +  str(newChiSquared) + Style.RESET_ALL + '\n')
            else:
                print(Fore.BLUE + 'New Χ^2 of '  +str(newChiSquared) + Style.RESET_ALL + '\n')


        ### Check new point against old
        if newChiSquared > chiSquareToMinimise:
            return self._lookAroundPointForSmallerChi2(phaseSpacePointDict, startTime, best_rSigma)
        else:
            return {'NewPointDict': newPointWithAttr, 'ChiSquared':newChiSquared}

    @regAlg
    def singleCellEvol( self ) :
        '''
        '''
        pointTree =  formatTopChi2List_asGen0( self.bestChiSquares, self.sortedChiSquare_ListOfTuples )


        alphaParents = list (pointTree.keys() )
        chi2Min = self.sortedChiSquare_ListOfTuples[0][1]
        genNb = 0

        listOfBestChi2 = [chi2Min]

        #### Selecting the best value for rSigma
        # smartRndGen = smartRand( {}, self.condDict, self.rndDict, {})
        # spinner = Halo(text='Getting the best rSigma.', spinner='dots')
        # spinner.start()
        # best_rSigma = smartRndGen.findBest_rSigma(pointTree[parentID]['Params'])
        # best_rSigma = 0.005


        best_rSigma = 0.0001
        best_rSigmaCutoff = 0.005

        best_rSigmaInit = best_rSigma
        justKicked = False

        chi2MinDict = {'GenNb-0': {'BestChi2':chi2Min , 'rSigmaVal':best_rSigma} }

        # rSigmaDict = {'Current_rSigma': best_rSigma, 'LastBest_rSigma': best_rSigma}


        while True:


            # Update the list?
            newParents = []
            pointCount = 0

            for parentID in alphaParents:

                pointNb = int(parentID.split('P')[1])


                # spinner.stop_and_persist(symbol=Fore.GREEN+'✔' + Style.RESET_ALL,
                #                              text = 'Got rSigma of ' + str(best_rSigma) )


                startTime = time.time()
                # spinner = Halo(text='Looking For a smaller Chi2', spinner='dots')
                # spinner.start()



                # pp(bestChiSquares[pointNb])
                # pp(pointTree[parentID]['FullDescription'])
                # exit()
                newPointDict = self._lookAroundPointForSmallerChi2(
                                                            pointTree[parentID]['FullDescription'],
                                                            startTime, best_rSigma
                                                            )
                # spinner.stop_and_persist(symbol=Fore.GREEN+'✔' + Style.RESET_ALL,
                #                              text = 'Got a smaller Chi2.')

                if newPointDict == None:
                    #### If we've timed out
                    if pointTree[parentID]['Parent'] != None:
                        newParents.append( pointTree[parentID]['Parent'] )
                    else:
                        newParents.append(parentID)
                    continue

                elif newPointDict['ChiSquared'] < pointTree[parentID]['Chi2']:

                    # {'NewPointDict': newPointWithAttr, 'ChiSquared':newChiSquared}
                    pointCount += 1

                    newPointKey = list(newPointDict['NewPointDict'].keys())[0]
                    newParamsDict = newPointDict['NewPointDict']
                    newChi2 = newPointDict['ChiSquared']


                    childID = 'G' + str(genNb + 1) + '-P' + str(pointCount)
                    pointTree.update (makeBranch( newPointDict['NewPointDict'],
                                                    newChi2, parentID, childID))
                    pointTree[parentID]['Children'].append( childID )
                    newParents.append( childID )

                    self.Que.put( newPointDict['NewPointDict'] )



            alphaParents = newParents

            chi2Min = pointTree[alphaParents[0]]['Chi2']
            minKey = alphaParents[0]



            for  newParent in alphaParents:
                if pointTree[newParent]['Chi2'] < chi2Min:
                    chi2Min = pointTree[newParent]['Chi2']
                    minKey = newParent


            genNb += 1
            # print ('\n' +'For gen# ' + str(genNb) +' the best χ² of ', chi2Min, ' from point :', minKey)
            # print(delimitator)

            print(delimitator2)
            print ('\n'+'For ' +Fore.GREEN+'Gen# ' + str(genNb)+ Style.RESET_ALL +' the best' +Fore.RED +  ' χ² of ', round(chi2Min,4) , Fore.BLUE + ' from ThreadNb :' + str(int(self.threadNumber)+1) , ' from point ', minKey )
            print(delimitator2)
            # printGenMsg(genNb, chi2Min, self.threadNumber, printStr, percChange)


            chi2MinDict.update( {'GenNb-'+str(genNb) : {'BestChi2': chi2Min, 'rSigmaVal': best_rSigma}  } )
            # pp(chi2MinDict)

            self.Que.put( {'GenNb': genNb,
                    'ThreadNb': int(self.threadNumber)+1,
                    'NewChi2': chi2Min,
                    'OldChi2': listOfBestChi2[-1]}
                )

            # If after genNbKill generations the chi2 measure hasn't changed by more than chi2PercCut percent then we increase the best_rSigma for the thread by a factor of amplificationFactor.
            chi2PercCut = 0.1
            genNbKill = 5
            amplificationFactor = 2.71828182846

            if genNb >= genNbKill:
                chi2ToCompare = chi2MinDict[ 'GenNb-' + str(genNb-genNbKill) ]['BestChi2']

                if ( (abs( chi2Min - chi2ToCompare )/ chi2ToCompare < chi2PercCut)
                    and (genNb % genNbKill == 0)
                     ):

                     best_rSigma = best_rSigma * amplificationFactor
                     justKicked = True
                     print(Fore.YELLOW + delimitator + Style.RESET_ALL)
                     printCentered('NEW rSigma value of ' + str(best_rSigma), color=Fore.YELLOW)
                     print(Fore.YELLOW + delimitator + Style.RESET_ALL)

            ##At some point by increasing rSigma enough we'll effectivelly land on a new region (which we define by best_rSigmaCutoff * amplificationFactor due to the lack of a better solution) we reset the rSigma value back to its initial value and restart the process.

            # #### NEED TO ADD COONDITION TO SEE IF THE NEW KICK HAS PRODUCED A SMALLER CHI 2
            # if best_rSigma > best_rSigmaCutoff * amplificationFactor:
            #     best_rSigma = best_rSigmaInit
            #
            #     print(Fore.GREEN + delimitator + Style.RESET_ALL)
            #     printCentered('Reset rSigma value to ' + str(best_rSigma), color=Fore.GREEN)
            #     print(Fore.GREEN + delimitator + Style.RESET_ALL)



            listOfBestChi2.append(chi2Min)
            del listOfBestChi2[0]
            if chi2Min < self.chi2LowerBound:
                self.Que.put( int(self.threadNumber)+1 )




        return None



algDict = regAlg.all


# @regAlg
# def diffEvol(psObject, q, bestChiSquares, sortedChiSquare_ListOfTuples,  threadNumber = '0', minimisationConstr='Global', timeOut = 120, ignoreConstrList = [], noOfSigmasB = 1, noOfSigmasPM = 1, debug= False,  chi2LowerBound = 1.0):
#     '''
#         Auxiliary multiprocessing function that will implement the differential evolution algorithm.
#     '''
#
#     modelConstr = constrEval( psObject )
#     pointTree =  formatTopChi2List_asGen0( bestChiSquares, sortedChiSquare_ListOfTuples )
#
#
#     alphaParents = list (  pointTree.keys() )
#
#     scanIDwThread = psObject.modelName + psObject.case.replace(" ","") + strftime("-%d-%m-%Y_%H_%M_%S", gmtime()) + '_ThreadNb' + threadNumber
#     resultsDirDicts = psObject.resultDir + 'Dicts/Focus' + strftime("_%d_%m_%Y/", gmtime())
#
#     # print(delimitator)
#     resultDict_Thread = {}
#
#
#     # chi2Min = sortedChiSquare_ListOfTuples[0][1]
#     # pp(sortedChiSquare_ListOfTuples[0])
#     # 'chi2Min': min( newListOfChi2 ),
#     # 'chi2Mean' : np.mean( newListOfChi2),
#     # 'chi2Std' : np.std( newListOfChi2)
#     chi2Vals = [chi2Tuple[1] for chi2Tuple in sortedChiSquare_ListOfTuples ]
#     listOfChi2StatDicts = [ { 'chi2Min': min(chi2Vals),
#             'chi2Mean': np.mean(chi2Vals) ,
#             'chi2Std': np.std(chi2Vals)
#                          } ]
#
#
#     listOfBestChi2 = [  sorted(sortedChiSquare_ListOfTuples, key=lambda tup: tup[1])[0][1]  ]
#     ####  Pick target vector at rndom / as lowestchi2? ####
#     # F_factor = 0.4
#     # CR_factor = 0.1
#
#     F_factor = 0.5
#     CR_factor = 0.1
#     generatingEngine = psObject.engineClass(psObject)
#
#
#
#     #### Initialisation stage ####
#     # Pick out 4 points in phase space and assign one of them as the target.
#
#     ### This population size multiplier seems slightly unnecessary
#     genPopSize = len(alphaParents)
#     genNb = 0
#     changeNb = 0
#
#
#     while True:
#
#         newParents = []
#         pointCount = 0
#
#         #### Populating the new generation. Stop when we have the same number of parents in the new one.
#         while len(newParents) < genPopSize:
#
#             for targetKey in alphaParents:
#
#
#
#                 # alphaParentsMod = deepcopy(alphaParents)
#                 # alphaParentsMod = [ parent for parent in alphaParents if parent != targetKey]
#                 rndKeyChoice = random.sample(alphaParents , 3)
#
#                 # targetKey = rndKeyChoice[0]
#                 targetChi2 = pointTree[targetKey]['Chi2']
#
#
#
#
#                 #### Mutation stage ####
#                 # Create a donnor vector out of the parameters of the 3 others via the formula below.
#                 donorDict = {}
#                 for modelParam in psObject.params.keys():
#                     xr1_Comp = pointTree[rndKeyChoice[0]][modelParam]
#                     xr2_Comp = pointTree[rndKeyChoice[1]][modelParam]
#                     xr3_Comp = pointTree[rndKeyChoice[2]][modelParam]
#
#                     # F_factor = random.uniform(0, 2)
#
#                     donorDict[modelParam] = xr1_Comp + F_factor * (xr2_Comp - xr3_Comp)
#
#                 # alphaParents = [parentPoint for parentPoint in alphaParents if parentPoint not in rndKeyChoice]
#
#
#
#                 #### Recombination stage ####
#                 # Make a new hybrid vector
#
#                 mutatedDict = {}
#                 rndParamChoice = random.choice(list(psObject.params.keys() ) )
#
#                 for modelParam in psObject.params.keys():
#
#                     if   random.uniform(0, 1) <= CR_factor or modelParam == rndParamChoice :
#                         # print ('_________--------\\\\\\\\')
#                         mutatedDict[modelParam] = donorDict[modelParam]
#                     else:
#                         # print('---------------------')
#                         mutatedDict[modelParam] = pointTree[targetKey][modelParam]
#
#
#
#
#                 ########### Selection stage ############
#
#                 genValidPointOutDict = generatingEngine.runPoint( mutatedDict, threadNumber = threadNumber , debug = debug)
#                 newPointWithAttr_int = generatingEngine._getRequiredAttributes(mutatedDict, threadNumber)
#                 newPointWithAttr = psObject._getCalcAttribForDict( newPointWithAttr_int )
#                 massTruth = generatingEngine._check0Mass( newPointWithAttr )
#
#
#
#                 if  massTruth == True:
#
#                     newPointKey = list(newPointWithAttr.keys())[0]
#
#                     newChiSquared = modelConstr.getChi2(
#                     newPointWithAttr[newPointKey], ignoreConstrList = ignoreConstrList, minimisationConstr = minimisationConstr, returnDict = False)
#                 else:
#                     newChiSquared = targetChi2 + 1
#
#
#                 # newPointWithAttr = generatingEngine._getRequiredAttributes(mutatedDict, threadNumber)
#                 ### New point evaluation
#
#                 # print(newChiSquared, targetChi2)
#                 # time.sleep(0.3)
#
#                 if newChiSquared < targetChi2:
#
#                     oldID = list(newPointWithAttr.keys())[0]
#                     pointGenID = oldID + '-GenNb'+ str(genNb)
#
#                     toAddDict = {}
#                     toAddDict[pointGenID] = newPointWithAttr[oldID]
#                     toAddChi2 = newChiSquared
#
#                     # print(toAddChi2, list(toAddDict.keys()) )
#                     with open( resultsDirDicts +'ScanResults.' + scanIDwThread + '.json', 'a') as outfile:
#                         json.dump(toAddDict, outfile)
#
#                 else:
#                     toAddDict = pointTree[targetKey]['FullDescription']
#                     toAddChi2 = targetChi2
#
#                 generatingEngine._clean( threadNumber )
#                 # print( delimitator )
#                 ### Add to the new generation
#                 pointCount += 1
#
#                 # newPointKey = list(newPointDict['NewPointDict'].keys())[0]
#                 # newParamsDict = newPointDict['NewPointDict']
#                 # newChi2 = newPointDict['ChiSquared']
#
#                 parentID = targetKey
#                 childID = 'G' + str(genNb + 1) + '-P' + str(pointCount)
#                 pointTree.update ( makeBranch( toAddDict, toAddChi2, parentID, childID) )
#
#                 pointTree[parentID]['Children'].append( childID )
#                 newParents.append( childID )
#
#                 # resultDict_Thread.update( toAddDict )
#
#
#
#                 # q.put( toAddDict )
#
#         #### Move on to the new generation ####
#         # print(len(newParents))
#         alphaParents = newParents
#         genNb += 1
#
#
#         ##### Getting the smallest Chi2 and sending it to the plotting function ####
#         chi2Min = pointTree[alphaParents[0]]['Chi2']
#         # minKey = alphaParents[0]
#
#         newListOfChi2 = []
#         for  newParent in alphaParents:
#             newListOfChi2.append(pointTree[newParent]['Chi2'])
#
#
#         chi2Min, chi2Mean , chi2Std=  min( newListOfChi2 ), np.mean( newListOfChi2), np.std( newListOfChi2)
#         # chi2Mean = np.mean( newListOfChi2)
#
#         newChi2Dict = {
#         'chi2Min': chi2Min,
#         'chi2Mean' : chi2Mean,
#         'chi2Std' : chi2Std,
#         'chi2List' : newListOfChi2 }
#
#             #
#             # if pointTree[newParent]['Chi2'] < chi2Min:
#             #     chi2Min = pointTree[newParent]['Chi2']
#             #     minKey = newParent
#
#         # pp(pointTree[minKey])
#         ############# Printing section ###########
#         quePut = False
#
#         if chi2Min < listOfBestChi2[-1]:
#             printStr = 'Minimum Decrease of'
#             percChange = round ( (chi2Min - listOfBestChi2[-1]) / listOfBestChi2[-1], 4) * 100
#             quePut = True
#
#             changeNb += 1
#
#             printGenMsg(genNb, chi2Min, threadNumber, printStr, percChange)
#
#             # print(delimitator2)
#             # print ('\n'+'For ' +Fore.GREEN+'Gen# ' + str(genNb)+ Style.RESET_ALL +
#             #         ' the best' + Fore.RED +  ' χ² of ', round(chi2Min,4) ,
#             #         Fore.YELLOW + ' from ThreadNb :' + str(int(threadNumber)+1) ,
#             #          # ' from point ', minKey ,
#             #         "   |   ", Fore.BLUE + printStr +  Style.RESET_ALL, percChange , '%' )
#             # print(delimitator2)
#         # elif chi2Min >  listOfBestChi2[-1]:
#         #     printStr = 'Increase of'
#
#         elif chi2Mean < listOfChi2StatDicts[-1]['chi2Mean']:
#             printStr = 'Distribution Mean Decrease of'
#             percChange = round ( (chi2Mean - listOfChi2StatDicts[-1]['chi2Mean']) /
#                                 listOfChi2StatDicts[-1]['chi2Mean'], 4) * 100
#
#             quePut = True
#             changeNb += 1
#             printGenMsg(genNb, chi2Min, threadNumber, printStr, percChange)
#
#
#         if quePut ==  True:
#             q.put( {'GenNb': genNb,
#                     'ThreadNb': int(threadNumber)+1,
#                     'NewChi2': chi2Min,
#                     'OldChi2': listOfBestChi2[-1],
#                     'NewChi2Dict': newChi2Dict ,
#                     'OldChi2Dict': listOfChi2StatDicts[-1] ,
#                     'ChangeNb': changeNb
#                     }
#                 )
#             with open(resultsDirDicts + 'GenStatus_ThreadNb'+ threadNumber +'.dat', 'a') as outFile:
#
#                 outFile.write(  ''.join(  attrName + str(attr)+'   ||  '
#                                         for attrName, attr in zip(['GenNb-', 'MinChi2: ', 'MeanChi2: ', 'StdChi2: '],
#                                                                   [genNb, chi2Min, chi2Mean, chi2Std])
#                                                     ) +'\n'  )
#
#         # print(delimitator2)
#         # print ('\n'+'For ' +Fore.GREEN+'Gen# ' + str(genNb)+ Style.RESET_ALL +
#         #         ' the best' + Fore.RED +  ' χ² of ', round(chi2Min,4) ,
#         #         Fore.YELLOW + ' from ThreadNb :' + str(int(threadNumber)+1) ,
#         #          # ' from point ', minKey ,
#         #         "   |   ", Fore.BLUE + printStr +  Style.RESET_ALL, percChange , '%' )
#         # print(delimitator2)
#
#         # chi2MinDict.update( {'GenNb-'+str(genNb) : {'BestChi2': chi2Min, 'rSigmaVal': best_rSigma}  } )
#         # pp(chi2MinDict)
#
#         # listOfBestChi2.append( newChi2Dict )
#         listOfChi2StatDicts.append( newChi2Dict )
#         listOfBestChi2.append(chi2Min)
#
#         del listOfBestChi2[0]
#         del listOfChi2StatDicts[0]
#
#         if chi2Min < chi2LowerBound:
#
#             print(Fore.RED + delimitator + Style.RESET_ALL)
#             printCentered('Hit χ² bound of '+str(chi2LowerBound) +   '   :::   Killing Thread #' + str(int(threadNumber)+1), color=Fore.RED)
#             print(Fore.RED + delimitator + Style.RESET_ALL)
#
#             # print(Fore.YELLOW + delimitator + Style.RESET_ALL)
#             q.put( int(threadNumber)+1 )
#             break
#
#
#
#     return None

# algDict = {'diffEvol' : diffEvol}
