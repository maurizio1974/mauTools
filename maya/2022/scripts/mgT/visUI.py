import maya.cmds as cmds
import maya.mel as mel


def mToolsVisUI(viewValue):

    viewValue;
    currentPanel = cmds.getPanel( wf = True )
    panelType = cmds.getPanel( currentPanel, to = True ) 
    i=0;
    attrs={"nurbsCurves":"Nurbs","nurbsSurfaces":"Surfaces","subdivSurfaces":"subD","polymeshes":"Polygons","planes":"Planes",
    "lights":"Lights","joints":"Joints","ikHandles":"ikHandles","deformers":"Deformers","dynamics":"Dynamics",       
    "fluids":"Fluids","hairSystems":"Hair","follicles":"Follicle","nCloths":"nCloths","nRigids":"nRigids",
    "dynamicConstraints":"DynConstr","locators":"Locators","dimensions":"Distance","pivots":"Pivots","handles":"Handles",
    "textures":"Textures","strokes":"Strokes","manipulators":"Manipulators","cameras":"Cameras","cv":"NurbsCV",
    "hulls":"NurbsHulls","grid":"Grid","hud":"HUD","sel":"Selection"}


    cmds.frameLayout(bs =( showFL, "etchedIn", cll = true, cl = 1, l = "Show", cc = ("showMode check 0;resizeWIN 3;"), ec = ("showMode check 0;resizeWIN 4;"), p = $mauUtyFLvis)
    cmds.formLayout(showFR)
    cmds.checkBox(radioAll, al "left", l "All", v 0, onc ("showMode -allObjects 1"), ofc ("showMode -allObjects 0"))
    cmds.checkBox(radioNone, al "left", l "None", v 0, onc ("showMode -allObjects 0"), ofc ("showMode -allObjects 1"))
    cmds.separator(sepaSH01, w 80, h 5, st "in")

    for e in attrs :
        if panelType == "modelPanel":
            viewValue = cmds.modelEditor -q ("-"+e) currentPanel`;
    
        cmds.checkBox( ("radio"+attrNames[i]), p = "showFR",al ="left", l = attrNames[i], v = viewValue, onc =("showMode -"+e+" 1"), ofc = ("showMode -"+e+" 0"))
        
        if ( panelType == "modelPanel" ):
            cmds.modelEditor -e ("-"+e) viewValue currentPanel;
        
        i=i+1
    
    cmds.formLayout(showFR, e=True,ap = [('radioNone','left',5,50),('radioSurfaces','left',5,50),('radioPolygons','left',5,50),
    ('radioLights','left',5,50),('radioikHandles','left',5,50),('radioDynConstr','left',5,50),('radioHair','left',5,50),
    ('radionCloths','left',5,50),('radioDeformers','left',5,50),('radioPivots','left',5,50),('radioDistance','left',5,50),
    ('radioTextures','left',5,50),('radioManipulators','left',5,50),('radioNurbsHulls','left',5,50),('radioGrid','left',5,50)],
    ac = [('sepaSH01','top',5,'radioAll'),('radioNurbs','top',5,'sepaSH01'),('radioSurfaces','top',5,'sepaSH01'),
    ('radiosubD','top',0,'radioNurbs'),('radioPolygons','top',0,'radioSurfaces'),('radioPlanes','top',0,'radiosubD'),
    ('radioLights','top',0,'radioPolygons'),('radioJoints','top',0,'radioPlanes'),('radioikHandles','top',0,'radioPlanes'),
    ('radioDynamics','top',0,'radioJoints'),('radioDynConstr','top',0,'radioikHandles'),('radioFluids','top',0,'radioDynamics'),
    ('radioHair','top',0,'radioDynConstr'),('radioFollicle','top',0,'radioFluids'),('radionCloths','top',0,'radioHair'),
    ('radionRigids','top',0,'radioFollicle'),('radioDeformers','top',0,'radionCloths'),('radioLocators','top',0,'radionRigids'),
    ('radioPivots','top',0,'radioDeformers'),('radioHandles','top',0,'radioLocators'),('radioDistance','top',0,'radioPivots'),
    ('radioCameras','top',0,'radioHandles'),('radioTextures','top',0,'radioDistance'),('radioStrokes','top',0,'radioCameras'),
    ('radioManipulators','top',0,'radioTextures'),('radioNurbsCV','top',0,'radioStrokes'),('radioNurbsHulls','top',0 ,'radioManipulators'),
    ('radioHUD','top',0,'radioNurbsCV'),('radioGrid','top',0,'radioNurbsHulls'),('radioSelection','top',0,'radioHUD')],
    af = [('radioAll','top',0),('radioAll','top',5),('radioNone','top',0),('sepaSH01','left',5),('sepaSH01','right',5),
    ('radioNurbs','left',5),('radiosubD','left',5),('radioPlanes','left',5),('radioJoints','left',5),('radioDynamics','left',5),
    ('radioFluids','left',5),('radioFollicle','left',5),('radionRigids','left',5),('radioLocators','left',5),('radioHandles','left',5),
    ('radioCameras','left',5),('radioStrokes','left',5),('radioNurbsCV','left',5),('radioHUD','left',5),('radioSelection','left',5)])