import time
import cv2
print(cv2.__version__)
import numpy as np
import pickle
import serial

arduinoData = serial.Serial('COM3', 9600)

class mpHands:
    import mediapipe as mp
    def __init__(self,max_num_hands=2,min_detection_confidence=0.5):
        self.hands=self.mp.solutions.hands.Hands(static_image_mode=False,max_num_hands=2,min_detection_confidence=0.5)
    def Marks(self,frame):
        myHands=[]
        frameRGB=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        results=self.hands.process(frameRGB)
        if results.multi_hand_landmarks != None:
            for handLandMarks in results.multi_hand_landmarks:
                myHand=[]
                for landMark in handLandMarks.landmark:
                    myHand.append((int(landMark.x*width),int(landMark.y*height)))
                myHands.append(myHand)
        return myHands
    
def findDistances(handData):
    distMatrix=np.zeros([len(handData),len(handData)],dtype='float')
    palmSize=((handData[0][0]-handData[9][0])**2+(handData[0][1]-handData[9][1])**2)**(1./2.)
    #*************palmSize**************#
    for row in range(0,len(handData)):
        for column in range(0,len(handData)):
            distMatrix[row][column]=(((handData[row][0]-handData[column][0])**2+(handData[row][1]-handData[column][1])**2)**(1./2.))/palmSize
    return distMatrix

def findError(gestureMatrix,unknownMatrix,keyPoints):
    error=0
    for row in keyPoints:
        for column in keyPoints:
            error=error+abs(gestureMatrix[row][column]-unknownMatrix[row][column])
    print(error)
    return error
def findGesture(unknownGesture,knownGestures,keyPoints,gestNames,tol):
    errorArray=[]
    for i in range(0,len(gestNames),1):
        error=findError(knownGestures[i],unknownGesture,keyPoints)
        errorArray.append(error)
    errorMin=errorArray[0]
    minIndex=0
    for i in range(0,len(errorArray),1):
        if errorArray[i]<errorMin:
            errorMin=errorArray[i]
            minIndex=i
    if errorMin<tol:
        gesture=gestNames[minIndex]
    if errorMin>=tol:
        gesture='Unknown'
    return gesture


width=640
height=360
cam=cv2.VideoCapture(0,cv2.CAP_DSHOW)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
cam.set(cv2.CAP_PROP_FPS, 30)
cam.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG'))
findHands=mpHands(1)
time.sleep(5)
keyPoints=[0,4,5,9,13,17,8,12,16,20]

train=int(input('Enter 1 to train enter 0 to regonize'))
if train==1:
    trainCnt=0
    knownGestures=[]

    numGest=int(input('How Many Gestures Do You Want? '))

    gestNames=[]

    for i in range(0,numGest,1):
        prompt='Name of Gesture #'+str(i+1)+' '
        name=input(prompt)
        gestNames.append(name)
    print(gestNames)
    trainName=input('What Training Data DO You Want To Use?(Press Enter For Default)')
    if trainName=='':
        trainName='default'
    trainName=trainName+'.pk'
if train==0:
    trainName=input('What Traing Datat Do You Want To Use?(Press Enter To Use Default)')
    if trainName=='':
        trainName='default'
    trainName=trainName+'.pk'
    with open(trainName,'rb') as f:
        gestNames=pickle.load(f)
        knownGestures=pickle.load(f)
tol=10
while True:
    ignore,  frame = cam.read()
    #frame=cv2.resize(frame,(width,height))
    handData=findHands.Marks(frame)
    if train==True:
        if handData!=[]:
            print('Please Show Gesture ',gestNames[trainCnt],': Press t when Ready')
            if cv2.waitKey(1) & 0xff==ord('t'):
                knownGesture=findDistances(handData[0])
                knownGestures.append(knownGesture)
                trainCnt=trainCnt+1
                if trainCnt==numGest:
                    train=0
                    with open(trainName,'wb') as f:
                        pickle.dump(gestNames,f)
                        pickle.dump(knownGestures,f)
    if train == 0:
        if handData!=[]:
            unknownGesture=findDistances(handData[0])
            myGesture=findGesture(unknownGesture,knownGestures,keyPoints,gestNames,tol)
            #error=findError(knownGesture,unknownGesture,keyPoints)            
            cv2.putText(frame,myGesture,(100,175),cv2.FONT_HERSHEY_SIMPLEX,3,(255,0,0),8)
            #*************send to port COM3******#
            myGesture=myGesture+'\r'
            arduinoData.write(myGesture.encode())
    
    for hand in handData:
        for ind in keyPoints:
            cv2.circle(frame,hand[ind],5,(34,100,34),-1)
    cv2.imshow('my WEBcam', frame)
    cv2.moveWindow('my WEBcam',0,0)
    if cv2.waitKey(1) & 0xff ==ord('q'):
        break
cam.release()