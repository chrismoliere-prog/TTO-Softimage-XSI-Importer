from dataclasses import dataclass


# global variables that are used in functions
counter = 0
layerTracker = 0
materialList = {}
textureList = []
modelList = {}
parentTracker = {}
envelopeDict = {}

# creates a model object generated from the mesh data passed to it, including materials and animation keyframes
@dataclass
class XsiModel:
    material: str
    transforms: list
    basepose: list
    visibility: bool
    constraints: dict
    modelType: str
    hasParent: bool
    parentName: str
    nurbsCurves: list
    vertices: dict
    polygons: list
    boneList: list
    clusters: list
    clusterWeights: dict
    animationFCurves: dict

# parses through entire file and assigns each si_object line a value
def nestTracker(lines):
    global parentTracker
    bracketTracker = -1
    for line in lines:
        if "{" in line:
            bracketTracker += 1
        if "}" in line:
            bracketTracker -= 1
        if "SI_Model" in line:
            lineName = getModelName(line, "SI_Model MDL-")
            if "Camera_Root" not in lineName:
                parentTracker[lineName] = bracketTracker

def modelEndTracker (lineSet):
    count = 0
    while count < (len(lineSet)-1):
        count += 1
        if "SI_Model" in lineSet[count]:
            break

    return count

# sets cutscene length based on passed information
def setCutSceneLength(xsiLines):
    # import counter
    global counter

    #define first frame of scene
    SceneStartFrame = xsiLines[counter + 2].replace(',', '')

    # define last frame
    SceneEndFrame = xsiLines[counter + 3].replace(',', '')

    # define FPS if option is available
    SceneFPS = xsiLines[counter + 4].replace(',', '')

    # skip unnecessary code lines
    counter += 4

    print(counter)
    # prints line to confirm all variables were successfully identified and saved
    print ("Scene starts at frame " + SceneStartFrame + " ends at frame " +
           SceneEndFrame + " and runs at " + SceneFPS, "FPS.")

# cleans up model name in file for use in Blender
def getModelName (line, inputString):
    name = line.replace(inputString, "").replace(" {", "").replace('",', '')
    return name

# uses materialList variable to generate a list of materials and the textures they use
def createMaterialList(lines):
    # import necessary global variables, and creates local term variable for storage
    global counter
    global materialList
    global textureList
    term = None

    while counter < len(lines):

        # if line denoting material is found, it is turned into a name for a material in the imported file and
        # saved into the global material dictionary (saved as key, value set to None for importing texture)
        if "XSI_Material " in lines[counter]:
            term = lines[counter].replace("XSI_Material DefaultLib.", "").replace(" {", "")
            materialList[term] = None
            print ("Found material " + term)

        # if an image is found, it is saved as the value to the corresponding key
        if "IMAGE" in lines[counter]:
            xsiTex = lines[counter].replace('"tex","','').replace('","IMAGE",', '')
            materialList[term] = xsiTex
            textureList.append(xsiTex)
            print ("Found texture " + xsiTex)

        # if a model (the next category) is found, the function ends and the print statements end
        if "SI_Model" in lines[counter]:
            print("Material parse complete, breaking loop.")
            print(materialList)
            print(textureList)
            break
        counter += 1

def createClusterList(lines):
    global envelopeDict
    envelopeCounter = 0
    listCounter = 0
    numberOfClusters = int(lines[1].replace(',', ''))
    envelopeCounter += 2
    listName = "0"
    while envelopeCounter < len(lines)-1:
        if listName not in lines[envelopeCounter]:
            listName = getModelName(lines[envelopeCounter], 'SI_Envelope ')
            envelopeDict[listName] = {}
        vertexDeformer = getModelName(lines[envelopeCounter + 2], '"MDL-')
        envelopeCounter += 3
        numberOfLines = int(lines[envelopeCounter].replace("," , ""))
        if numberOfLines != 0:
            tupleList = lines[envelopeCounter+1:numberOfLines+1+envelopeCounter]
            nestedDict = list(item.rstrip(", ").split(",") for item in tupleList)
            nestedDict =  [tuple(float(num) for num in sublist) for sublist in nestedDict]
            tempDict = {vertexDeformer:nestedDict}
            envelopeDict[listName].update(tempDict)
        envelopeCounter += (numberOfLines + 2)
        if listCounter < numberOfClusters:
            listCounter += 1
        else:
            break
    return envelopeDict


def clusterToClass():
    global modelList
    global envelopeDict
    for item in envelopeDict.keys():
        modelList[item].clusterWeights = envelopeDict[item]
    return modelList




def modelFunc(name, lines, modelParam, count):
    modelMaterial = modelType = ""
    modelBasePose = modelTransforms = modelBoneList = curvePointList = boneClusters = []
    vertexDict = {}
    polyDict = []
    animDict = {}
    modelVisibility = False
    hasParent = False

    tracker = 0
    modelConstraints = {}

    while tracker < count:
        # finds material model uses, cleans up string for blender to easily read
        if "SI_GlobalMaterial" in lines[tracker]:
            tracker += 1
            modelMaterial = lines[tracker].replace('"DefaultLib.', '').replace('",', '')
            modelParam = "\n".join([modelParam, ("modelMaterial is " + modelMaterial)])

        # toggles visibility of model
        if "SI_Visibility" in lines[tracker]:  # Sets value for model visibility
            tracker += 1
            if "1" in lines[tracker]:
                modelVisibility = True
                modelParam = "\n".join([modelParam, "Model is Visible"])
            else:
                modelVisibility = False
                modelParam = "\n".join([modelParam, "Model is Hidden"])

        # if model is a null modelType is changed to null
        if "SI_Null" in lines[tracker]:
            modelType = "Null"
            modelParam = "\n".join([modelParam, "Model Type defined as Null"])

        # if the model is a mesh modelType is defined as a mesh
        if "SI_Mesh" in lines[tracker]:  # Define model Mesh
            print(lines[tracker])
            modelType = "Mesh"
            modelParam = "\n".join([modelParam, "Model Type defined as Mesh"])

            # trackers number of lists for values (vertex locations, individual vert normals, uv map locations)
            numberOfLists = int(lines[tracker + 2].replace(',', ''))

            # define value for parsing through lists, that resets when function is recalled
            value = 0

            # skip to lists
            tracker += 4

            # creates lists specified by list tracker (normals are not exported but may be implemented later)
            while value < numberOfLists:
                listName = lines[tracker + 1].replace(',', '').replace('"', '')
                print (listName)
                numberOfLines = int(lines[tracker].replace(',', ''))
                if "Texture_Projection" in lines[tracker+2]:
                    listLines = lines[tracker + 3:tracker + (numberOfLines+3)]
                else:
                    listLines = lines[tracker + 2:tracker + (numberOfLines + 2)]
                listLines = [item.rstrip(",").replace(",", ", ").replace('"', '') for item in listLines]
                listLines = [tuple(float(num) for num in item.split(",")) for item in listLines]
                print (len(listLines))
                vertexDict[listName] = listLines
                value += 1
                modelParam = "\n".join([modelParam, ("Mesh " + listName + " Vertices: " + "\n" + str(listLines))])
                # print ("Mesh " + listName + " Vertices: " + "\n" + str(listLines))
                if "Texture_Projection" not in lines[tracker + 2]:
                    tracker += numberOfLines + 2
                else:
                    tracker += numberOfLines + 3
            print ('completed')


        # Makes list of curve points if necessary
        if "XSI_CurveList" in lines[tracker]:
            modelType = "Curve"
            modelParam = "\n".join([modelParam, "Model Type defined as Curve"])
            tracker += 7
            curvePointTracker = int(lines[tracker].replace(",", "").replace('"', ''))
            curvePointList = lines[tracker + 1:tracker + curvePointTracker + 1]
            curvePointList = [item.rstrip(",") for item in curvePointList]
            curvePointList.insert(0, curvePointList.pop())
            modelParam = "\n".join([modelParam, "Model curve points are: " + "\n" + str(curvePointList)])

        # Adds the number of vertices per polygon, and which vertex indices are used for which face
        if "SI_PolygonList" in lines[tracker]:
            polyLength = int(lines[tracker + 1].replace(",", ""))
            polyVertTracker = lines[tracker + 4:tracker + (polyLength + 4)]
            polyVertTracker = [item.rstrip(",").replace(",", "") for item in polyVertTracker]
            modelParam = "\n".join([modelParam, ("Number of Faces: " + "\n" + str(polyLength))])
            tracker += polyLength + 5
            faceVertices = lines[tracker:tracker + polyLength]
            faceVertices = [item.rstrip(",").replace(",", ", ").replace('"', '') for item in faceVertices]
            faceVertices = [tuple(int(num) for num in item.split(",")) for item in faceVertices]
            polyDict = list(faceVertices)
            modelParam = "\n".join([modelParam, ("Model polygon vert counts per face are: " + "\n" + str(
                polyVertTracker) + "\n" + "Model vertices per face are: " + "\n" + str(faceVertices))])

        # identifies transform values for the model as it currently is, includes Base Pose if there is one
        if "SI_Transform" in lines[tracker]:
            # creates list of transform positions if it is found in line
            transforms = list(lines[tracker + 1:tracker + 10])
            transforms = [item.replace(",", "") for item in transforms]
            transforms = [float(i) for i in transforms]

            # depending on if it's the basePose or standard rotation the list gets saved to a different class value
            if "SRT" in lines[tracker]:
                modelTransforms = transforms
                modelParam = "\n".join([modelParam, ("ModelTransforms are: " + "\n" + str(modelTransforms))])
            if "BASEPOSE" in lines[tracker]:
                modelBasePose = transforms
                modelParam = "\n".join([modelParam, ("ModelBasePoses are: " + "\n" + str(modelBasePose))])
            tracker += 10

        # if constraint is found, creates name for constraint node and
        # defines constraint object/what's being affected
        if "SI_Constraint" in lines[tracker]:
            constrainedObject = lines[tracker + 1].replace(",", "").replace('"', '')
            constraintName = lines[tracker].replace("SI_Constraint ", "").replace(' {', '')
            constraintProp = lines[tracker + 2].replace(",", "").replace('"', '')
            constrainingObject = lines[tracker + 4].replace(",", "").replace('"', '')
            tracker += 4
            objectConstraints = [constrainedObject, constraintProp, constrainingObject]
            modelConstraints[constraintName] = objectConstraints
            modelParam = "\n".join([modelParam, (
                        str(objectConstraints[1]) + " of " + objectConstraints[0] + " is being constrained by " +
                        objectConstraints[2] + " using constraint " + constraintName)])

        # if the following strings are found, the names are cleaned up and the mesh type is identified as a bone
        # for the root the empty is given a name and a list showing the bone chain and effector are created
        if "SI_IK_Root" in lines[tracker]:
            rootName = lines[tracker].replace(" {", "").replace('"', '')
            listInt = lines[tracker+1].replace(',', '')
            boneTracker = int(lines[tracker + 1].replace(',', ''))
            tracker += 2
            modelRoot = list(lines[tracker:tracker + boneTracker + 1])
            modelRoot = [line.replace(",", "").replace('"', '') for line in modelRoot]
            modelRoot.insert(0, listInt)
            modelType = "IK_Root"
            modelBoneList = modelRoot
            modelParam = "\n".join([modelParam, ("IK Chain found, consisting of root" + rootName + "and chain" + str(
                modelRoot[:-1]) + "ending with effector" + str(modelRoot[-1]))])

        # if IK joints are found their individual transforms are added, converted to floats, and saved
        if "SI_IK_Joint" in lines[tracker]:
            tracker += 2
            modelJoints = list(lines[tracker:tracker + 14])
            modelJoints = [item.replace(",", "") for item in modelJoints]
            modelJoints = [float(i) for i in modelJoints]
            tracker += 14
            modelType = "IK_Joint"
            modelBoneList = modelJoints

        # if the property is for an effector only the name is needed
        # Identifies ending empty of IK Chain
        if "SI_IK_Effector" in lines[tracker]:
            tracker += 1
            effectorValue = int(lines[tracker].replace(',', ''))
            modelType = "IK_Effector"
            modelParam = "\n".join([modelParam, ("IK Chain effector is " + str(effectorValue))])

        #generate curves/keyframes
        if "SI_FCurve" in lines[tracker]:
            curvePropName = lines[tracker+2].replace(",", "").replace('"', '')
            curvePointNumber = int (lines[tracker+6].replace(",", ""))
            curvePointList = list(lines[tracker+7:(tracker+curvePointNumber+7)])
            curvePointList = [line.rstrip(",") for line in curvePointList]
            curvePointList = [[float(num) for num in item.split(",")] for item in curvePointList]
            animDict[curvePropName] = curvePointList
            modelParam = "\n".join([modelParam, ("Animation curve points for " + curvePropName + " are:" +
            "\n" + str(curvePointList))])
            tracker += (curvePointNumber + 7)

        if "SI_Cluster" in lines[tracker]:
            clusterListLength = int (lines[tracker+4].replace(",", ""))
            clusterList = lines[tracker+5:(tracker+5+clusterListLength)]
            boneClusters = clusterList
            modelParam = "\n".join([modelParam, ("Cluster list has " + str(clusterListLength) +
            " points for Envelope Weights, which are: " + "\n" + str(clusterList))])
            tracker += (clusterListLength + 5)

        if "SI_EnvelopeList" in lines[tracker]:
            print("all models parsed, breaking out")
            break

        tracker += 1
    tempClassObject = XsiModel(modelMaterial, modelTransforms, modelBasePose, modelVisibility, modelConstraints,
    modelType, hasParent, "", curvePointList, vertexDict, polyDict,
    modelBoneList, boneClusters, {}, animDict)
    modelList[name] = tempClassObject
    return modelList

# function for creating all models, generates name and subset of properties
def createModel(lines, intern):
    # global variables
    global modelList
    global materialList #imports global variables
    modelParam = ""

    siModelName = getModelName(lines[intern], "SI_Model MDL-")
    modelLineList = list(lines[intern:len(lines)])
    modelEndLength = modelEndTracker(modelLineList)
    modelParam = modelFunc(siModelName, modelLineList, modelParam, modelEndLength)
    #modelParam = siModelName + modelParam + "\n"
    return modelParam

#function that iterates through the 2 dictionaries, and determines each objects parent and if they are parented
def setChild (modelLists, trackerDict):
    tracker = 0

    #returns the names of all models in dictionary
    nameList = list(modelLists)
    currentParent = ""
    currentName = ""
    matchingNestList = []
    while tracker < len(nameList):

        # gets current level of depth based on the name determined by the counter value, which in turn is used to
        # get the nest depth value associated with that name
        nestLevel = (trackerDict[nameList[tracker]])
        if nestLevel != trackerDict[nameList[tracker-1]]:
            # a list is made of all keys in the dictionary that share the same current nest value
            matchingNestList = list(dict({k: v for k, v in trackerDict.items() if v == nestLevel}))
        #if the level does not equal zero, the parent flag is set to true
        if nestLevel != 0:
            modelLists[nameList[tracker]].hasParent = True

        # if the current level is equivalent to that of the previous level + 1 (1 level deeper) the previous item
        # is set as the parent, and stored in a string for the next if statement
        if nestLevel ==  (trackerDict[nameList[tracker-1]]+1):
            currentParent = nameList[tracker-1]
            modelLists[nameList[tracker]].parentName = nameList[tracker-1]

        # if the current object's nest level is the same as the one that came before it, they're both set
        # to share the same parent
        elif nestLevel == (trackerDict[nameList[tracker-1]]):
            modelLists[nameList[tracker]].parentName = currentParent

        # if the current object is at a higher level than the one before it, the parent is set to share
        # the parent of the previous model to be at that level
        elif nestLevel < (trackerDict[nameList[tracker-1]]):
            currentName = nameList[tracker]
            index = int (matchingNestList.index(currentName))
            previousMatchingEntry = str(matchingNestList[index-1])
            modelLists[nameList[tracker]].parentName = modelLists[previousMatchingEntry].parentName
            currentParent = modelLists[nameList[tracker]].parentName
        else:
            modelLists[nameList[tracker]].hasParent = False
        currentName = nameList[tracker]
        index = int(matchingNestList.index(currentName))
        previousMatchingEntry = str(matchingNestList[index - 1])
        tracker += 1
    return modelLists
#reset all global vars to default values
def reset_variables():
    global counter, layerTracker, materialList, textureList, modelList, parentTracker, envelopeDict
    counter = 0
    layerTracker = 0
    materialList = {}
    textureList = []
    modelList = {}
    parentTracker = {}
    envelopeDict = {}

# function that activates all functions and parses through file
def importXSI(xsiFile):
    # global variable
    reset_variables()
    global counter

    # opens selected xsi file, and eliminates all unnecessary characters (empty lines, tabs, etc.)
    with open(xsiFile) as filePath:
        lines = [line.strip() for line in filePath if line.strip()]
        nestTracker(lines)

    # if the first line defines the file as xsi, the program deems it safe to continue
    if "xsi" in lines[0]:
        print("No Issues. continue")


    # triggers certain functions depending on substring in line, and moves counter forward once subfunctions are done
    # loop continues until the end of the file is reached, internal functions will also advance progress by
    # manually adding to counter to skip lines
    while counter < len(lines):
        if "SI_Scene" in lines[counter]:
            setCutSceneLength(lines)
        if "SI_MaterialLibrary" in lines[counter]:
            createMaterialList(lines)
        if "MDL-Camera_Root" in lines[counter]:
            counter += 50
        if "SI_Model" in lines[counter]:
            createModel(lines, counter)
        if "SI_EnvelopeList" in lines[counter]:
            tempList = list(lines[counter:len(lines)])
            createClusterList(tempList)
            clusterToClass()

        counter += 1
    setChild(modelList, parentTracker)
    return modelList
