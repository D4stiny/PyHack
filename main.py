'''
Copyright 2017 Robater - https://www.unknowncheats.me/forum/members/656078.html

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

from ctypes import *
from memorpy import *
import time
import win32api
import random
import thread
import win32gui
import math
import winsound

# OFFSET START #
crossHairIDOffset = 0xAA70
forceAttackOffset = 0x2F0917C
forceJumpOffset = 0x4F5FD5C
clientStateOffset = 0x5CA524
clientStateViewAnglesOffset = 0x4D0C
aimPunchOffset = 0x301C
clientStateInGameOffset = 0x100
flagsOffset = 0x100
vecOriginOffset = 0x134
shotsFiredOffset = 0xA2C0

entityListOffset = 0x04AC91B4
localPlayerIndexOffset = 0x178
localPlayerOffset = 0xAA66D4
glowObjectOffset = 0x4FE3A5C
glowIndexOffset = 0xA320
teamNumOffset = 0xF0
dormantOffset = 0xE9
healthOffset = 0xFC
bSpottedOffset = 0x939
# OFFSET END #

# OPTIONS START #
glowESPEnabled = True
triggerBotEnabled = True
autoBHOPEnabled = True
soundESPEnabled = True
rcsEnabled = True

maxSoundESPDistance = 780 # Default: 780, decent distance tbh
RCSPerfectPercent = 100 # Percent of RCS being perfect, 100% = perfect RCS
triggerBotKey = 0x12 # Default: right-click
triggerBotRandomMinimum = 50 # Minimum miliseconds to wait before shooting, there is a random int between 0-50 added to this in the code
# OPTIONS END #

foundProcess = False
end = False
csgoWindow = None

# triggerBot: if entity in crosshair is an enemy, fire with a random delay between triggerBotRandomMinimum miliseconds to triggerBotRandomMinimum + 50 miliseconds
def triggerBot(process, client, clientState):
    global end
    global csgoWindow
    while not end: # This function is threaded so might as well do this :>
        time.sleep(0.01)
        if not win32gui.GetForegroundWindow():
            continue
        if win32gui.GetForegroundWindow() == csgoWindow:
            if Address((clientState + clientStateInGameOffset), process).read('int') == 6: # If the client is in game
                localPlayer = Address((client + localPlayerOffset), process).read() # Get LocalPlayer
                localPlayerTeam = Address((localPlayer + teamNumOffset), process).read('int') # Get the team of the LocalPlayer

                crossHairID = Address((localPlayer + crossHairIDOffset), process).read('int') # Get the Entity ID of the entity in crosshairs
                if crossHairID == 0: # If no entity in crosshair
                    continue

                crossEntity = Address((client + entityListOffset + ((crossHairID - 1) * 0x10)), process).read() # Find entity based on ID defined by crossHairID

                crossEntityTeam = Address((crossEntity + teamNumOffset), process).read('int') # Get team of Entity in Crosshair

                if crossEntityTeam != 2 and crossEntityTeam != 3: # If the entity is not a terrorist or counter-terrorist
                    continue

                crossEntityDormant = Address((crossEntity + dormantOffset), process).read('int') # Get boolean that states whether entity in crosshair is dormant or not

                if win32api.GetAsyncKeyState(triggerBotKey) and localPlayerTeam != crossEntityTeam and crossEntityDormant == 0: # if triggerBotKey is held, the localPlayers team is not equal to entity in crosshair's team, and if the entity in crosshair is not dormant
                    time.sleep((triggerBotRandomMinimum + random.randint(0, 50)) / 1000.0) # Sleep for random delay between triggerBotRandomMinimum miliseconds to triggerBotRandomMinimum + 50 miliseconds
                    while crossHairID != 0 and win32api.GetAsyncKeyState(triggerBotKey): # while there is an entity in my crosshairs and my triggerbot key is held down
                        crossHairID = Address((localPlayer + crossHairIDOffset), process).read('int') # Re-get the crosshair ID to check if maybe no longer an entity in my crosshair
                        Address((client + forceAttackOffset), process).write(5, 'int') # Shoot
                        time.sleep(0.01) # Sleep for 10 ms
                        Address((client + forceAttackOffset), process).write(4, 'int') # Stop shooting

# normalizeAngles: Normalize a pair of angles
def normalizeAngles(viewAngleX, viewAngleY):
    if viewAngleX < -89.0:
        viewAngleX = 89.0
    if viewAngleX > 89.0:
        viewAngleX = 89.0
    if viewAngleY < -180.0:
        viewAngleY += 360.0
    if viewAngleY > 180.0:
        viewAngleY -= 360.0

    return viewAngleX, viewAngleY

# glowESP: Enables glow around each entity
def glowESP(process, client):
    glowLocalBase = Address((client + localPlayerOffset), process).read() # Get the localPlayer
    glowPointer = Address((client + glowObjectOffset), process).read() # Get the glow Pointer
    myTeamID = Address((glowLocalBase + teamNumOffset), process).read('int') # Get the localPlayer team ID

    playerCount = Address((client + glowObjectOffset + 0x4), process).read('int')
    for i in range(1, playerCount): # For each player until the max players available
        glowCurrentPlayer = Address((client + entityListOffset + ((i - 1) * 0x10)), process).read() # Get current entity based on for-loop variable i

        if glowCurrentPlayer == 0x0: # If the entity is invalid
            break # Break out of the for loop, we have reached the current max players

        glowCurrentPlayerDormant = Address((glowCurrentPlayer + dormantOffset), process).read('int') # Get boolean that states whether glowCurrentPlayer entity is dormant or not
        glowCurrentPlayerGlowIndex = Address((glowCurrentPlayer + glowIndexOffset), process).read('int') # Get the glowIndex of the glowCurrentPlayer entity

        entityBaseTeamID = Address((glowCurrentPlayer + teamNumOffset), process).read('int') # Get the team ID of the glowCurrentPlayer entity

        if entityBaseTeamID == 0 or glowCurrentPlayerDormant != 0: # If the glowCurrentPlayer entity is on an irrelevant team (0) or if the glowCurrentPlayer entity is dormant
            continue # Continue the for-loop
        else:
            if myTeamID != entityBaseTeamID: # If localPlayer team is not glowCurrentPlayer entity team
                Address((glowCurrentPlayer + bSpottedOffset), process).write(1, 'int')  # Set glowCurrentPlayer bspotted to True

            # fucking nigger python with no switch statements kill me
            if entityBaseTeamID == 2: # If glowCurrentPlayer entity is a terrorist
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x4)), process).write(1.0, 'float')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x8)), process).write(0.0, 'float')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0xC)), process).write(0.0, 'float')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x10)), process).write(1.0, 'float')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x24)), process).write(1, 'int')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x25)), process).write(0, 'int')
            elif entityBaseTeamID == 3: # else if glowCurrentPlayer entity is a counter-terrorist
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x4)), process).write(0.0, 'float')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x8)), process).write(0.0, 'float')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0xC)), process).write(1.0, 'float')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x10)), process).write(1.0, 'float')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x24)), process).write(1, 'int')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x25)), process).write(0, 'int')
            else:
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x4)), process).write(0.0, 'float')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x8)), process).write(1.0, 'float')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0xC)), process).write(0.0, 'float')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x10)), process).write(1.0, 'float')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x24)), process).write(1, 'int')
                Address((glowPointer + ((glowCurrentPlayerGlowIndex * 0x38) + 0x25)), process).write(0, 'int')

# BHOP: Automatically start jumping if in game, on the ground, and space is held
def BHOP(process, client, localPlayer, clientState):
    global end
    global csgoWindow

    while not end:
        if win32gui.GetForegroundWindow() == csgoWindow and Address((clientState + clientStateInGameOffset), process).read('int') == 6: # If client is in game
            flags = Address((localPlayer + flagsOffset), process).read() # Get client flags
            if flags & (1 << 0) and win32api.GetAsyncKeyState(0x20): # If localPlayer on the ground and if space is held
                Address((client + forceJumpOffset), process).write(6, 'int') # Autojump
            flags = Address((localPlayer + flagsOffset), process).read() # Get the latest flags again
        time.sleep(0.01)

def soundESP(process, client, localPlayer):
    global maxSoundESPDistance
    global end
    global csgoWindow

    while not end:
        time.sleep(0.01)

        if win32gui.GetForegroundWindow() == csgoWindow:
            closestPlayer = 99999.0
            playerCount = Address((client + glowObjectOffset + 0x4), process).read('int')
            for i in range(0, playerCount):
                ent = Address((client + entityListOffset + ((i - 1) * 0x10)), process).read()  # Get current entity based on for-loop variable i

                if ent is 0x0:
                    break

                entDormant = Address((ent + dormantOffset), process).read('int') # Get boolean that states whether glowCurrentPlayer entity is dormant or not

                if entDormant != 0:
                    continue

                myTeamID = Address((localPlayer + teamNumOffset), process).read('int') # Get the team ID of the localPlayer
                entityBaseTeamID = Address((ent + teamNumOffset), process).read('int')  # Get the team ID of the ent entity

                if entityBaseTeamID != 2 and entityBaseTeamID != 3:
                    continue

                localPlayerX = Address((localPlayer + vecOriginOffset), process).read('float') # Get the X coordinate of the vecOrigin of the localPlayer
                localPlayerY = Address((localPlayer + vecOriginOffset + 0x4), process).read('float') # Get the Y coordinate of the vecOrigin of the localPlayer
                localPlayerZ = Address((localPlayer + vecOriginOffset + 0x8), process).read('float') # Get the Z coordinate of the vecOrigin of the localPlayer

                entityX = Address((ent + vecOriginOffset), process).read('float') # Get the X coordinate of the vecOrigin of the ent
                entityY = Address((ent + vecOriginOffset + 0x4), process).read('float') # Get the Y coordinate of the vecOrigin of the ent
                entityZ = Address((ent + vecOriginOffset + 0x8), process).read('float') # Get the Z coordinate of the vecOrigin of the ent

                distance = math.sqrt((pow((entityX - localPlayerX), 2) + pow((entityY - localPlayerY), 2) + pow((entityZ - localPlayerZ), 2))) # Get the distance between localPlayer and ent

                if myTeamID != entityBaseTeamID and distance != 0 and closestPlayer > distance: # If not on localPlayer team and team is either 2 or 3 and distance isnt 0 and distance is less than closestPlayer
                    closestPlayer = distance

            if closestPlayer != 99999.0 and closestPlayer < maxSoundESPDistance: # If closestPlayer isnt default value and closestPlayer is closer than maxSoundESPDistance
                durMath = 1.000/maxSoundESPDistance # Generate baseline mathematical thingy - use ur brain
                winsound.Beep(2500, int((durMath * closestPlayer) * 1000))

def RCS(process, client, clientState):
    oldAimPunchX = 0 # Initializing var (going to be used to store the last aimPunchX)
    oldAimPunchY = 0 # Initializing var (going to be used to store the last aimPunchY)
    global RCSPerfectPercent # Defines how much RCS we are gonna do

    while True:
        if win32gui.GetForegroundWindow() == csgoWindow and Address((clientState + clientStateInGameOffset), process).read('int') == 6: # If we are actually playing in game
            localPlayer = Address((client + localPlayerOffset), process).read() # Get the localPlayer
            if Address((localPlayer + shotsFiredOffset), process).read('int') > 1: # If we have fired more than 1 shots
                viewAngleX = Address((clientState + clientStateViewAnglesOffset), process).read('float') # Get the X viewAngle
                viewAngleY = Address((clientState + clientStateViewAnglesOffset + 0x4), process).read('float') # Get the Y viewAngle

                aimPunchX = Address((localPlayer + aimPunchOffset), process).read('float') # Get the X aimPunch
                aimPunchY = Address((localPlayer + aimPunchOffset + 0x4), process).read('float') # Get the Y aimPunch

                viewAngleX -= (aimPunchX - oldAimPunchX) * (RCSPerfectPercent * 0.02) # Subtract our AimPunch from our ViewAngle
                viewAngleY -= (aimPunchY - oldAimPunchY) * (RCSPerfectPercent * 0.02) # Subtract our AimPunch from our ViewAngle

                viewAngleX, viewAngleY = normalizeAngles(viewAngleX, viewAngleY) # Normalize our ViewAngles

                Address((clientState + clientStateViewAnglesOffset), process).write(viewAngleX, 'float')
                Address((clientState + clientStateViewAnglesOffset + 0x4), process).write(viewAngleY, 'float')

                oldAimPunchX = aimPunchX
                oldAimPunchY = aimPunchY
            else:
                oldAimPunchX = 0
                oldAimPunchY = 0
        time.sleep(0.01)

def getDLL(name, PID):
    hModule = CreateToolhelp32Snapshot(TH32CS_CLASS.SNAPMODULE, PID)
    if hModule is not None:
        module_entry = MODULEENTRY32()
        module_entry.dwSize = sizeof(module_entry)
        success = Module32First(hModule, byref(module_entry))
        while success:
            if module_entry.th32ProcessID == PID:
                if module_entry.szModule == name:
                    return module_entry.modBaseAddr
            success = Module32Next(hModule, byref(module_entry))

        CloseHandle(hModule)
    return 0

# main: Main function, starts all the threads, does glow esp, waits for end key, etc :)
def main():
    global triggerBotEnabled
    global autoBHOPEnabled
    global glowESPEnabled
    global soundESPEnabled
    global end
    global csgoWindow
    global rcsEnabled

    processHandle = Process(name="csgo") # Get csgo process
    if not processHandle: # If handle is bad
        print("CSGO not found. Exiting.") # CSGO wasn't found ;''''(
        exit(1)

    print("CSGO found, getting necessary modules.")
    client = getDLL("client.dll", processHandle.pid) # Get client.dll module
    print("Got client.dll.")

    engine = getDLL("engine.dll", processHandle.pid) # Get engine.dll module
    print("Got engine.dll.")

    print("Hack started, press END to exit.")

    clientState = Address((engine + clientStateOffset), processHandle).read() # Get clientState pointer
    localPlayer = Address((client + localPlayerOffset), processHandle).read() # Get localPlayer pointer

    csgoWindow = win32gui.FindWindow(None, "Counter-Strike: Global Offensive")
    if csgoWindow is None:
        print("The CSGO Window was not found.")
        exit(1)

    if triggerBotEnabled:
        try:
            thread.start_new_thread(triggerBot, (processHandle, client, clientState, )) # Start triggerBot function threaded
        except:
            print("Could not start triggerbot thread :(")

    if autoBHOPEnabled:
        try:
            thread.start_new_thread(BHOP, (processHandle, client, localPlayer, clientState, )) # Start BHOP function threaded
        except:
            print("Could not start bhop thread :(")


    if soundESPEnabled:
        try:
            thread.start_new_thread(soundESP, (processHandle, client, localPlayer, )) # Start soundESP function threaded
        except:
            print("Could not start playerCounter thread :(")

    if rcsEnabled:
        try:
            thread.start_new_thread(RCS, (processHandle, client, clientState,))  # Start RCS function threaded
        except:
            print("Could not start rcs thread :(")

    while not win32api.GetAsyncKeyState(0x23): # While END key isn't touched
        if Address((clientState + clientStateInGameOffset), processHandle).read('int') == 6: # If client is in game
            if glowESPEnabled and win32gui.GetForegroundWindow() == csgoWindow:
                glowESP(processHandle, client) # Call glowESP function non-threaded
            time.sleep(0.01)
    end = True # Tells the threads to stop looping, prevents future problems
    time.sleep(0.01)

if __name__ == "__main__":
    main()