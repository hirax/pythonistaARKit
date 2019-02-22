# coding: utf-8
# Jun Hirabayashi (jun@hirax.net, twitter @hirax)
# This code is based on Brun0oO's work(MIT License)
# https://github.com/Brun0oO/Pythonista/blob/master/arkit/main.py
# and Charles Surett's work.
# https://github.com/scj643/objc_tools/blob/master/objc_tools/scenekit/sk_scene.py
# Following thread will be heplful for understanding how Pythonista can call ARKit.
# https://forum.omz-software.com/topic/4362/solved-first-attempt-to-integrate-arkit-and-first-questions/29

# info
# https://blog.pusher.com/building-an-ar-app-with-arkit-and-scenekit/
# http://www.cl9.info/entry/2017/10/07/110000

import ui, os, sys, time, math
#from math import *
from enum import IntFlag

from objc_util import *
from objc_tools.scenekit.util import SUPPORTED_FORMATS, LightType, ShadowMode, DebugOptions, RenderingAPI, LightingModel
from objc_tools.scenekit.structures import Vector3, Vector4, Matrix4
from objc_tools.ui.editorview import TabView, tabVC

load_framework('SceneKit')
load_framework('ARKit')
load_framework('SpriteKit')

SCNNode = ObjCClass('SCNNode')
SCNLight = ObjCClass('SCNLight')
SCNSphere = ObjCClass('SCNSphere')
SCNBox = ObjCClass('SCNBox')
SCNCone = ObjCClass('SCNCone')
SCNCapsule = ObjCClass('SCNCapsule')
SCNCylinder = ObjCClass('SCNCylinder')

SCNScene = ObjCClass('SCNScene')
SCNNode = ObjCClass('SCNNode')
SCNLight = ObjCClass('SCNLight')
SCNView = ObjCClass('SCNView')
SCNCamera = ObjCClass('SCNCamera')
UIViewController = ObjCClass('UIViewController')
SCNMaterial = ObjCClass('SCNMaterial')

# ------------ SeneKit View -----------------
class SKView (object):
    '''SKView
        This object is used for subclassing
    '''
    def __init__(self):
        self._create_objc()
        self.attach()
    
    def _create_objc(self):
        self._scene_objc = SCNView.alloc().initWithFrame_options_(((0, 0),(100, 100)), ns({'SCNViewOptionPreferredRenderingAPI': 1})).autorelease()
        self._scene_objc.setAutoresizingMask_(18) # Fill superview
        self._scene_objc.setNeedsDisplayOnBoundsChange_(True) # fill on change
        self._scene_ref = None
        self._pointOfView_ref = Node(self._scene_objc.pointOfView())
    
    def attach(self):
        '''attach
            This function is called after __init__
            '''
        pass
    
    @property
    def showsStatistics(self):
        return self._scene_objc.showsStatistics()
    
    @showsStatistics.setter
    def showsStatistics(self, state):
        if type(state) == bool:
            self._scene_objc.setShowsStatistics_(state)
        else:
            raise TypeError('Must be a bool')

    @property
    def preferredFramesPerSecond(self):
        return self._scene_objc.preferredFramesPerSecond()
    
    @preferredFramesPerSecond.setter
    def preferredFramesPerSecond(self, value):
        self._scene_objc.setPreferredFramesPerSecond_(value)
    
    @property
    def allowsCameraControl(self):
        return self._scene_objc.allowsCameraControl()
    
    @allowsCameraControl.setter
    def allowsCameraControl(self, state):
        if type(state) == bool:
            self._scene_objc.setAllowsCameraControl_(state)
        else:
            raise TypeError('Must be a bool')

    @property
    def scene(self):
        if self._scene_ref:
            return self._scene_ref
        elif self._scene_objc.scene():
            raise Warning('The scene does not have a reference')
            return Scene(self._scene_objc.scene())
        else:
            return None

    @scene.setter
    def scene(self, value):
        if isinstance(value, (Scene)):
            self._scene_ref = value
            self._scene_objc.setScene_(value._objc)
        elif isinstance(value, (ObjCInstance)):
            self._scene_ref = Scene(value)
            self._scene_objc.setScene_(value)
        else:
            raise TypeError("Not able to set scene")

    @property
    def debugOptions(self):
        return DebugOptions(self._scene_objc.debugOptions())
    
    @debugOptions.setter
    def debugOptions(self, value):
        if isinstance(value, (DebugOptions)):
            self._scene_objc.setDebugOptions_(value.value)
        else:
            self._scene_objc.setDebugOptions_(int(value))

    @property
    def pointOfView(self):
        if self._scene_objc.pointOfView().ptr != self._pointOfView_ref._objc.ptr:
            self._pointOfView_ref = Node(self._scene_objc.pointOfView())
        return self._pointOfView_ref
    
    def setPointOfView(self, value, animate = True):
        if isinstance(value, (ObjCInstance)):
            self._pointOfView_ref = Node(value)
            self._scene_objc.setPointOfView_animate_(value, animate)
        if isinstance(value, (Node)):
            self._pointOfView_ref = value
            self._scene_objc.setPointOfView_animate_(value._objc, animate)

    def stop(self):
        self._scene_objc.stop_(None)
    
    def pause(self):
        self._scene_objc.pause_(None)
    
    def play(self):
        self._scene_objc.play_(None)

#--------Scene View---------
class SceneView (SKView):
	
    def attach(self):
        self.uiView = ui.View()
        self.present = self.uiView.present
        ObjCInstance(self.uiView).addSubview_(self._scene_objc)

#--------Scene Tab---------
class SceneTab (SceneView, TabView):
	
    def __init__(self):
        SceneView.__init__(self)
        TabView.__init__(self)
    
    @on_main_thread
    def makeSelf(self):
        self.name = "SceneKit"
    
    @on_main_thread
    def customVC(self):
        return create_objc_class(
                     "CustomViewController",
                     UIViewController,
                     methods = [],
                     protocols = ["OMTabContent"],
                   ).new()
    
    @on_main_thread
    def show(self):
        self.newVC.View = ObjCInstance(self.uiView)
        self.newVC.title = self.name
        self.newVC.navigationItem().rightBarButtonItems = self.right_button_items
        tabVC.addTabWithViewController_(self.newVC)

#--------Scene---------
class Scene (object):
	
    def __init__(self, scene = None):
        if scene:
            self._objc = objc
        else:
            self._objc = SCNScene.scene()
        self._node_ref = Node(self._objc.root())
    
    @property
    def playbackSpeed(self):
        return self._objc.playbackSpeed()
    
    @playbackSpeed.setter
    def playbackSpeed(self, value):
        self._objc.setPlaybackSpeed_(value)
    
    @property
    def framerate(self):
        return self._objc.frameRate()
    
    @framerate.setter
    def framerate(self, value):
        self._objc.setFrameRate_(value)
    
    @property
    def fogDensityExponent(self):
        '''
            Controls the attenuation between the start and end fog distances.
            0 means a constant fog, 1 a linear fog and 2 a quadratic fog,
            but any positive value will work.
            '''
        return self._objc.fogDensityExponent()
    
    @fogDensityExponent.setter
    def fogDensityExponent(self, value):
        self._objc.setFogDensityExponent_(value)
    
    @property
    def fogStartDistance(self):
        return self._objc.fogStartDistance()
    
    @fogStartDistance.setter
    def fogStartDistance(self, value):
        self._objc.setFogStartDistance_(value)
    
    @property
    def fogEndDistance(self):
        return self._objc.fogEndDistance()
    
    @fogEndDistance.setter
    def fogEndDistance(self, value):
        self._objc.setFogEndDistance_(value)
    
    @property
    def paused(self):
        return self._objc.isPaused()
    
    @paused.setter
    def paused(self, value):
        self._objc.setPaused_(value)
    
    @property
    def node(self):
        if self._node_ref._objc.ptr == self._objc.root().ptr: # checks so we domt use more memory
            return self._node_ref
        else:
            self._node_ref = Node(self._objc.root())
            return self._node_ref

    def removeAllParticleSystems(self):
        self._objc.removeAllParticleSystems()
    
    def save_to_file(self, file_name):
        if SUPPORTED_FORMATS.match(path.rsplit('.', 1)[-1]):
            options = ns({'SCNSceneExportDestinationURL': nsurl(path)})
            file = nsurl(file_name)
            
            return self._objc.writeToURL_options_(url, options)
        else:
            raise TypeError('Not a supported export type')

    def __repr__(self):
        return '<Scene <Framerate: {}, node: {}>>'.format(self.framerate, self.node)

# ------ Node ----------
class Node (object):
    def __init__(self, objc = None):
        self._light = None
        self._geometry = None
        self._camera = None
        self._child_ref = []
        if objc:
            self._objc = objc
            if self._objc.light():
                self._light = Light(objc=self._objc.light())
            if self._objc.geometry():
                self._geometry = Geometry(self._objc.geometry())
            if self._objc.camera():
                self._camera = Camera(self._objc.camera())
        else:
            self._objc = SCNNode.node()

    @property
    def childNodes(self):
        return self._child_ref
    
    @property
    def name(self):
        if self._objc.name():
            return str(self._objc.name())
        else:
            return None
    
    @name.setter
    def name(self, value):
        self._objc.setName_(value)
    
    @property
    def scale(self):
        return self._objc.scale()
    
    @scale.setter
    def scale(self, value):
        self._objc.setScale_(value)
    
    @property
    def transform(self):
        '''transfrom
            Note: with this you can not set properties directly
            '''
        return self._objc.transform(argtypes = [], restype = Matrix4)
    
    @transform.setter
    def transform(self, value):
        self._objc.setTransform_(value, argtypes = [Matrix4], restype = None)
    
    @property
    def position(self):
        return self._objc.position(argtypes = [], restype = Vector3)
    
    @position.setter
    def position(self, value):
        self._objc.setPosition_(value, argtypes = [Vector3], restype = None)
    
    @property
    def rotation(self):
        return self._objc.rotation()
    
    @rotation.setter
    def rotation(self, value):
        self._objc.setRotation_(value)
    
    @property
    def light(self):
        return self._light
    
    @light.setter
    def light(self, value):
        if isinstance(value, (ObjCInstance)):
            self._objc.setLight_(value)
            self._light = Light(value)
        if isinstance(value, (Light)):
            self._objc.setLight_(value._objc)
            self._light = value
        if value == None:
            self._objc.setLight_(value)
            self._light = value
    
    @property
    def geometry(self):
        return self._geometry
    
    @geometry.setter
    def geometry(self, value):
        if isinstance(value, (ObjCInstance)):
            self._objc.setGeometry_(value)
            self._geometry = Geometry(value)
        if isinstance(value, (Geometry)):
            self._objc.setGeometry_(value._objc)
            self._light = value
        if value == None:
            self._objc.setGeometry_(value)
            self._light = value
    
    @property
    def camera(self):
        return self._camera
    
    @camera.setter
    def camera(self, value):
        if isinstance(value, (ObjCInstance)):
            self._objc.setCamera_(value)
            self._camera = Camera(value)
        if isinstance(value, (Camera)):
            self._objc.setCamera_(value._objc)
            self._camera = value
        if value == None:
            self._objc.setCamera_(value)
            self._camera = value
    
    def clone(self):
        '''clone
            The copy is recursive: every child node will be cloned, too.
            The copied nodes will share their attached objects (light, geometry, camera, ...) with the original instances
            '''
        clone = self._objc.clone()
        return Node(clone)
    
    def flattenedClone(self):
        '''flattenedCLone
            A copy of the node with all geometry combined
            '''
        clone = self._objc.flattenedClone()
        return Node(clone)
    
    def addChild(self, value):
        if isinstance(value, (ObjCInstance)):
            if self._objc.canAddChildNode_(value):
                self._objc.addChildNode_(value)
                self._child_ref += [Node(value)]
        if isinstance(value, (Node)):
            if self._objc.canAddChildNode_(value._objc) and value not in self._child_ref:
                self._objc.addChildNode_(value._objc)
                self._child_ref += [value]

#--------- Light ------------
class Light (object):
	
    def __init__(self, kind = LightType.Omni, casts_shadow = True, shadow_sample_count = 1000, objc = None):
        if objc:
            self._objc = objc
        else:
            self._objc = SCNLight.light()
            self.type = kind
            self.castsShadow = casts_shadow
            self.shadowSampleCount = shadow_sample_count

    @property
    def type(self):
        return self._objc.type()
    
    @type.setter
    def type(self, kind):
        self._objc.setType_(kind)
    
    @property
    def castsShadow(self):
        return self._objc.castsShadow()
    
    @castsShadow.setter
    def castsShadow(self, value):
        self._objc.setCastsShadow_(value)
    
    @property
    def intensity(self):
        return self._objc.intensity()
    
    @intensity.setter
    def intensity(self, value):
        self._objc.setIntensity_(value)
    
    @property
    def shadowSampleCount(self):
        return self._objc.shadowSampleCount()
    
    @shadowSampleCount.setter
    def shadowSampleCount(self, value):
        self._objc.setShadowSampleCount_(value)
    
    @property
    def name(self):
        if self._objc.name():
            return str(self._objc.name())
        else:
            return None
    
    @name.setter
    def name(self, value):
        self._objc.setName_(value)
    
    @property
    def color(self):
        return self._objc.color()
    
    @color.setter
    def color(self, value):
        self._objc.setColor_(value)
    
    @property
    def shadowColor(self):
        return self._objc.color()
    
    @shadowColor.setter
    def shadowColor(self, value):
        self._objc.setShadowColor_(value)
    
    @property
    def shadowRadius(self):
        return self._objc.shadowRadius()
    
    @shadowRadius.setter
    def shadowRadius(self, value):
        self._objc.setShadowRadius(value)
    
    @property
    def shadowMapSize(self):
        return self._objc.shadowMapSize()
    
    @shadowMapSize.setter
    def shadowMapSize(self, value):
        self._objc.setShadowMapSize(value)

#--------- Camera ------------
class Camera (object):
	
    def __init__(self, objc = None):
        if objc:
            self._objc = objc
        else:
            self._objc = SCNCamera.camera()

    @property
    def name(self):
        if self._objc.name():
            return str(self._objc.name())
        else:
            return None
    
    @name.setter
    def name(self, value):
        self._objc.setName_(value)
    
    @property
    def xFov(self):
        '''Setting to 0 resets it to normal'''
        return self._objc.xFov()
    
    @xFov.setter
    def xFov(self, value):
        self._objc.setXFov_(value)
    
    @property
    def yFov(self):
        '''Setting to 0 resets it to normal'''
        return self._objc.yFov()
    
    @yFov.setter
    def yFov(self, value):
        self._objc.setYFov_(value)

# ---------- geometry ----------------
class Geometry (object):
	
    def __init__(self, objc = None):
        self._objc = objc
    
    @property
    def name(self):
        if self._objc.name():
            return str(self._objc.name())
        else:
            return None
    
    @name.setter
    def name(self, value):
        self._objc.setName_(value)
    
    @property
    def material(self):
        return Material(self._objc.material())


# --------- Material ------------
class Material (object):
	
    def __init__(self, objc = None):
        self._objc = objc
    
    @property
    def lightingModel(self):
        return str(self._objc.lightingModelName())
    
    @lightingModel.setter
    def lightingModel(self, value):
        if type(value) == str:
            self._objc.setLightingModelName_(value)
        else:
            print('not a valid type')

def load_scene(file):
    url = ns(file)
    s = SCNScene.sceneWithURL_options_(url, ns({}))
    return Scene(s)

#---------------
# Some 'constants' used by ARkit

class ARWorldAlignment(IntFlag):
    ARWorldAlignmentGravity = 0
    ARWorldAlignmentGravityAndHeading = 1
    ARWorldAlignmentCamera = 2

class ARPlaneDetection(IntFlag):
    ARPlaneDetectionNone = 0
    ARPlaneDetectionHorizontal = 1 << 0
    ARPlaneDetectionVertical = 1 << 1

# Work In Progress here, I(Brun0oO's)'m deciphering the ARKit constants...
#class ARSCNDebugOption(IntFlag):
#    ARSCNDebugOptionNone = 0
#    ARSCNDebugOptionShowWorldOrigin = int("ffffffff80000000", 16)
#    ARSCNDebugOptionShowFeaturePoints = int("ffffffff40000000", 16)

class ARSessionRunOptions(IntFlag):
    ARSessionRunOptionsNone                     = 0
    ARSessionRunOptionResetTracking             = 1 << 0
    ARSessionRunOptionRemoveExistingAnchors     = 1 << 1

NSError = ObjCClass('NSError')
SCNScene = ObjCClass('SCNScene')
ARSCNView = ObjCClass('ARSCNView')
ARWorldTrackingConfiguration = ObjCClass('ARWorldTrackingConfiguration')
ARSession = ObjCClass('ARSession')
UIViewController = ObjCClass('UIViewController')
ARPlaneAnchor = ObjCClass('ARPlaneAnchor')

sceneview = None

#========= setup an initial scene ===================
def createSampleScene():
    global scene
    global root_node
    global cube_node
    scene = SCNScene.scene()
    root_node = scene.rootNode()
    cube_node = [] # jun , particles
    
    # setup lights
    distanceOfLight = 1000
    light = SCNLight.light()
    light.setType_('omni')
    light.setType_('directional')
    light.setColor_( ObjCClass('UIColor').colorWithRed_green_blue_alpha_(0.8,1.0,0.9,1.0) )
    light_node = SCNNode.node()
    light_node.setLight_(light)
    light_node.setPosition((distanceOfLight, distanceOfLight, distanceOfLight))
    root_node.addChildNode_(light_node)

    light2 = SCNLight.light()
    light2.setType_('omni')
    light2.setColor_( ObjCClass('UIColor').colorWithRed_green_blue_alpha_(1.0,0.7,0.9,1.0) )    
    light_node2 = SCNNode.node()
    light_node2.setLight_(light2)
    light_node2.setPosition((-distanceOfLight, distanceOfLight, -distanceOfLight))
    root_node.addChildNode_(light_node2)
    
    light3 = SCNLight.light()
    light3.setType_('omni')
    light3.setColor_( ObjCClass('UIColor').colorWithRed_green_blue_alpha_(0.7,0.7,1.0,1.0) )    
    light_node3 = SCNNode.node()
    light_node3.setLight_(light3)
    light_node3.setPosition((distanceOfLight, distanceOfLight, -distanceOfLight))
    root_node.addChildNode_(light_node3)
    
    return scene

def setDebugOptions(arscn):
    #val = ARSCNDebugOption.ARSCNDebugOptionShowWorldOrigin | ARSCNDebugOption.ARSCNDebugOptionShowFeaturePoints
    val = int("fffffffffc000000", 16) # this value is a combination of ShowWorldOrigin and ShowFeaturePoints flags, but I can't isolate each flags....
    ##val = int("fffffffff0000000", 16) # this value is a combination of ShowWorldOrigin and ShowFeaturePoints print('Before calling setDebugOptions_(%s) : debugOptions=%s' %(hex(val), hex(arscn.debugOptions())))
    
    #arscn.setDebugOptions_(val)   # make axis and featurepoints clear
    print('After calling setDebugOptions_(%s) : debugOptions=%s' % (hex(val),hex(arscn.debugOptions())))

def createARSceneView(x, y, w, h, debug=True):
    v = ARSCNView.alloc().initWithFrame_((CGRect(CGPoint(x, y), CGSize(w, h))))
    v.setShowsStatistics_(debug) # I love statistics...
    return v

#============ touch event ===========================================
def CustomViewController_touchesBegan_withEvent_(_self, _cmd, _touches, event):
    touches = ObjCInstance(_touches)
    for t in touches:
        loc = t.locationInView_(sceneview)
        sz = ui.get_screen_size()
        print(loc)  # touch の場所次第で終了する

    global cube_node # jun
    global root_node
    global gnum
    global scene

    aType, aColor, aSize, aLength, aMatrix = createNodeElementInfo()

    #cube_geometry = SCNBox.boxWithWidth_height_length_chamferRadius_(0.02, 0.02, 0.02, 0)
    #cube_geometry.material.lightingModel = LightingModel.PhysicallyBased # 追加したけど動かない

    Material = SCNMaterial.material()
    Material.contents = ObjCClass('UIColor').colorWithRed_green_blue_alpha_(aColor[0],aColor[1],aColor[2],aColor[3])
    Material.lightingModel = LightingModel.PhysicallyBased

    if 'sphere' == aType:
        sphere_geometry = SCNSphere.sphereWithRadius_(aSize)
        sphere_geometry.setMaterials_([Material])
        cube_node.append( SCNNode.nodeWithGeometry_(sphere_geometry) )
        cube_node[gnum].position = gPosition
        root_node.addChildNode_( cube_node[gnum] )
        gnum = gnum + 1
    if 'arrow' == aType:
        sphere_geometry = SCNCone.coneWithTopRadius_bottomRadius_height_(0,aSize/5.0,aSize/2.0)
        sphere_geometry.setMaterials_([Material])
        cube_node.append( SCNNode.nodeWithGeometry_(sphere_geometry) )
        cube_node[gnum].position = gPosition
        cube_node[gnum].rotation = aMatrix
        root_node.addChildNode_( cube_node[gnum] )
        gnum = gnum + 1
        sphere_geometry2 = SCNCapsule.capsuleWithCapRadius_height_(aSize/20.0,aLength)
        #sphere_geometry2 = SCNCone.coneWithTopRadius_bottomRadius_height_(0,aSize/10.0,aSize)
        sphere_geometry2.setMaterials_([Material])
        cube_node.append( SCNNode.nodeWithGeometry_(sphere_geometry2) )
        cube_node[gnum].position = gPosition
        #cube_node[gnum].setPosition((gPosition.x+aMatrix.x*(0.001), gPosition.y+aMatrix.y*(0.001), gPosition.z+aMatrix.z*(0.001)))
        cube_node[gnum].rotation = aMatrix
        root_node.addChildNode_( cube_node[gnum] )
        gnum = gnum + 1

@on_main_thread

def runARSession( arsession ):
    global garsession # jun
    garsession = arsession	
    arconfiguration = ARWorldTrackingConfiguration.alloc().init()
    arconfiguration.setPlaneDetection_(ARPlaneDetection.ARPlaneDetectionHorizontal)
    arconfiguration.setWorldAlignment_(ARWorldAlignment.ARWorldAlignmentGravity)
    arsession.runWithConfiguration_options_( arconfiguration, ARSessionRunOptions.ARSessionRunOptionResetTracking | ARSessionRunOptions.ARSessionRunOptionRemoveExistingAnchors )

    time.sleep(0.5) # Let the system breathe ;o)
    print('configuration', arsession.configuration())

def CustomViewController_viewWillAppear_(_self, _cmd, animated):
    return

def CustomViewController_viewWillDisappear_(_self, _cmd, animated):
    session = sceneview.session()
    session.pause()

def MyARSCNViewDelegate_renderer_didAdd_for_(_self, _cmd, scenerenderer, node, anchor):
    if not isinstance(anchor, (ARPlaneAnchor)):
        return
    # to be implemented...
    # SCNSceneRenderer, willRenderScene scene: SCNScene, atTime time: TimeInterval) {
    # renderer(_ renderer: SCNSceneRenderer, willRenderScene scene: SCNScene, atTime time: TimeInterval) {

#-------------- willRenderScene_atTime (obtaining camera matrix) -------------------------
def MyARSCNViewDelegate_renderer_willRenderScene_atTime_(_self, _cmd, scenerenderer, scene, time):
    # camera matrix parameters are obtained here (jun)
    pointOfView = sceneview.pointOfView()
    transform = pointOfView.transform()
    global gRotation, gPosition
    gRotation = pointOfView.rotation()
    gPosition = pointOfView.position()
    gTransform = pointOfView.transform()
    #global gcamx, gcamy, gcamz
    #gcamx = gPosition.x
    #gcamy = gPosition.y
    #gcamz = gPosition.z
    #rotx =  gRotation.x
    #roty =  gRotation.y
    #rotz =  gRotation.z
    #rotw =  gRotation.w
    return

def MyARSCNViewDelegate_session_didFailWithError_(_self,_cmd,_session,_error):
    print('error',_error,_cmd,_session)
    err_obj=ObjCInstance(_error)
    print(err_obj)

# I(jun) don't need those information at this moment.
#def MyARSCNViewDelegate_session_didUpdate_(_self,_cmd,_session,_error):
#    print(_err)

# The main class...
class MyARView(ui.View):
    def __init__(self):
        super().__init__(self)

    @on_main_thread
    def initialize(self):
        self.flex = 'WH'
        screen = ui.get_screen_size()
        # set up the ar scene view delegate
        methods = [ MyARSCNViewDelegate_renderer_didAdd_for_, MyARSCNViewDelegate_session_didFailWithError_,
                    MyARSCNViewDelegate_renderer_willRenderScene_atTime_ ]
        protocols = [ 'ARSCNViewDelegate' ]
        MyARSCNViewDelegate = create_objc_class('MyARSCNViewDelegate', NSObject, methods=methods, protocols=protocols)
        delegate = MyARSCNViewDelegate.alloc().init()

        # set up the ar scene view
        global sceneview
        sceneview = createARSceneView(0, 0, screen.width, screen.height)
        global scene
        sceneview.scene = scene
        sceneview.setDelegate_(delegate)

        # set up the custom view controller
        methods = [CustomViewController_touchesBegan_withEvent_, CustomViewController_viewWillAppear_, CustomViewController_viewWillDisappear_]
        protocols = []
        CustomViewController = create_objc_class('CustomViewController', UIViewController, methods=methods, protocols=protocols)
        cvc = CustomViewController.alloc().init()
        cvc.view = sceneview

        # internal kitchen
        self_objc = ObjCInstance(self)
        self_objc.nextResponder().addChildViewController_(cvc)
        self_objc.addSubview_(sceneview)
        cvc.didMoveToParentViewController_(self_objc)

        # here, we try...
        runARSession( sceneview.session() )
        
        setDebugOptions(sceneview)

    def will_close(self):
        session = sceneview.session()
        session.pause()

# template for returning ('sphere' or 'arrow'), (r,g,b,a), size, length, matrix
def createNodeElementInfo():
    return 'sphere', [1.0, 0.0, 0.0, 1.0], 0.02, 0.02, 0

# globals to be defined
garsession = None; gnum = 0; gPosition = None; gRotation = None; gTransform = None

#==================================================================
if __name__ == '__main__':

    import motion; motion.start_updates()

    def createNodeElementInfo():
        a = motion.get_gravity()
        return 'arrow', [a[0], pow(abs(a[0]-0.5),1.5), 1.0-a[0], 0.8], 1, 0.05+pow(a[0],4)*10.0, gRotation

    scene =  createSampleScene()
    v = MyARView()
    v.present('full_screen', hide_title_bar=True, orientations=['portrait'])
    v.initialize()
