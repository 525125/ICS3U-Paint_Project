# Scott Xu
# paint_project.py
# This is my version of Microsoft Paint. The canvas is in the middle of the screen, and is the only section
# that the user can make changes to. On the left side is a toolbar with two tabs and a colour palette. The user
# is able to select and use different tools as well as the colour they want to work with. On the right side are
# stamps that the user can place on the canvas. The user can also undo their last edit, clear the canvas to
# start over, and load or save a canvas from or to a bitmap file. The mouse position and a short description
# of the current tool are also given. There is music playing in the background.

###########################################################################

from tkinter import *
from pygame import *
from random import *
from math import *

###########################################################################

# functions for tools
def line_points(oldx, oldy, mx, my): # list of points between (oldx, oldy) and (mx, my)
    ans = []
    dist = max(abs(mx-oldx), abs(my-oldy))
    if dist == 0:
        ans.append((mx, my))
    for i in range(dist): # use similar triangles to find integer coordinates
        newx = int(oldx+i*(mx-oldx)/dist)
        newy = int(oldy+i*(my-oldy)/dist)
        ans.append((newx, newy))
    return ans

def spray_paint(mx, my, radius, colour): # spray paint effect for a given point
    for i in range(radius):
        x = randint(0-radius, radius)
        y = randint(0-radius, radius)
        if hypot(x, y) <= radius: # make sure pixel is in the circle
            screen.set_at((mx+x, my+y), colour)
            
def glitter_pt(mx, my, radius, colour): # glitter effect for a given point
    x = randint(0-radius, radius)
    y = randint(0-radius, radius)
    r = randint(1, 3)
    if hypot(x, y)+r <= radius:
        draw.circle(screen, colour, (mx+x, my+y), r)
        
def bucket_fill(mx, my, oldColour, newColour, screen): # fill an area with the given colour
    # i.e. checks if each pixel is the original colour; if so, fills it in and checks its four adjacent pixels
    if oldColour != newColour:
        points = {(mx, my)}
        checked = set()
        while len(points) > 0:
            point = points.pop()
            if point not in checked:
                try:
                    if screen.get_at(point) == oldColour:
                        screen.set_at(point, newColour)
                        x, y = point
                        points.add((x-1, y))
                        points.add((x+1, y))
                        points.add((x, y-1))
                        points.add((x, y+1))
                except:
                    pass
                checked.add(point)
                
def incomplete_polygon(points, colour): # draw an incomplete polygon with the given points
    # i.e. draws a line between every pair of adjacent points in the list, but not between the first and last points
    for i in range(len(points)-1):
        x1, y1 = points[i]
        x2, y2 = points[i+1]
        for j in line_points(x1, y1, x2, y2):
            draw.circle(screen, colour, j, 2)
        
def blur_circ(x, y, canvasRect): # blur a circle with radius 20 around a point
    # i.e. sets each point in the circle as the average colour of its adjacent pixels
    cornerX, cornerY = x-20, y-20 # top left corner of the circle's circumscribed square
    blurSurf = screen.subsurface(Rect(cornerX, cornerY, 40, 40)).copy()
    blurSurf.set_colorkey((0, 1, 1, 0)) # for pixels not in the circle
    for i in range(41):
        for j in range(41):
            if hypot(i-20, j-20) <= 20: # (i,j) on blurSurf corresponds to (cornerX+i,cornerY+j) on screen
                # find the r, g, and b values of the pixel's adjacent points, then take their averages
                xs = [k+cornerX for k in (i-1, i+1, i, i)]
                ys = [k+cornerY for k in (j, j, j-1, j+1)]
                r,g,b = [],[],[]
                for k in range(4):
                    if canvasRect.collidepoint(xs[k], ys[k]):
                        colour = screen.get_at((xs[k], ys[k]))
                        r.append(colour.r)
                        g.append(colour.g)
                        b.append(colour.b)
                if len(r) > 0: # r, g, and b have the same number of elements
                    avgR = sum(r)//len(r)
                    avgG = sum(g)//len(g)
                    avgB = sum(b)//len(b)
                    blurSurf.set_at((i, j), (avgR ,avgG, avgB))
            else:
                blurSurf.set_at((i, j), (0, 1, 1, 0))
    screen.blit(blurSurf, (cornerX, cornerY))
    
def pixel(x, y, canvasRect): # pixelate a 5 x 5 square around a given point
    # i.e. fills a 5 x 5 square with the average colour of its pixels
    x, y = x - x%5, y - y%5 # so the squares line up
    # the following algorithm for the average rgb value is similar to the one used in the blur function
    r, g, b = [], [], []
    for i in range(x, x+5):
        for j in range(y, y+5):
            if canvasRect.collidepoint(i, j):
                colour = screen.get_at((i, j))
                r.append(colour.r)
                g.append(colour.g)
                b.append(colour.b)
    if len(r) > 0: # r, g, and b have the same number of elements
        avgR = sum(r)//len(r)
        avgG = sum(g)//len(g)
        avgB = sum(b)//len(b)
        draw.rect(screen, (avgR, avgG, avgB), (x, y, 5, 5))
        
def cutout(selection_pts): # cut out polygon (for selection tool)
    xs, ys = zip(*selection_pts)
    minX, maxX = min(xs), max(xs)
    minY, maxY = min(ys), max(ys)
    new_pts = [(i-minX, j-minY) for (i, j) in selection_pts] # "shift" points to fit on a smaller surface
    selectRect = Rect((minX, minY, maxX-minX+1, maxY-minY+1))
    select_surface = screen.subsurface(selectRect).copy() # smallest surface that contains the whole polygon
    select_surface.set_colorkey((0, 1, 0, 0))
    shape_surface = Surface((maxX-minX+1, maxY-minY+1))
    shape_surface.fill((0, 1, 0, 0)) # second surface filled with the first surface's colorkey
    shape_surface.set_colorkey((0, 1, 1, 0))
    draw.polygon(shape_surface, (0, 1, 1, 0), new_pts) # transparent polygon drawn on second surface
    select_surface.blit(shape_surface, (0, 0)) # when the 2nd surface is blitted over the 1st, the selected
                                             # polygon remains visible while the rest becomes transparent
    return select_surface

###########################################################################

# basic display screen
root = Tk()
root.withdraw()
screen = display.set_mode((1250, 750))
display.set_caption('Celestial Paint')

# play music
init()
try:
    mixer.music.load("music/The Edge Of Forever.mp3") # works on school computer, but not on Mac
    mixer.music.play(-1)
except:
    pass

# pre-defined colours
boxColour = (216,1,17) # colour for borders
toolbarColour = (198, 215, 242) # colour for toolbars
toolbarDark = (98,115,142) # colour for unselected toolbar page
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# fonts
trebuchetFont14 = font.SysFont("trebuchetms", 14, bold = True)
texttoolFont = font.SysFont("trebuchetms", 20, bold = True) # font for text tool
logoFont = font.SysFont("trebuchetms", 115, bold = True) # text for logo
timesFont30 = font.SysFont("timesnewroman", 30)
titleFont = font.SysFont("trebuchetms", 15, bold = True) # font for names of tools
descriptionFont = font.SysFont("trebuchetms", 12) # font for tool descriptions

# background image
background = image.load("images/background.jpg")
screen.blit(background, (0, 0))

# canvas
draw.rect(screen, WHITE, (250, 150, 750, 550))
draw.rect(screen, boxColour, (248, 148, 754, 554), 3)
canvasRect = Rect(250, 150, 750, 550) # Rect for canvas

# left toolbar
draw.rect(screen, toolbarColour, (50, 150, 150, 550))
draw.rect(screen, boxColour, (48, 148, 154, 554), 3)
draw.line(screen, boxColour, (50, 422), (200, 422), 4)
draw.line(screen, boxColour, (50, 527), (200, 527), 4)

# left toolbar page selection
toolbar_tab1 = Rect(27, 150, 20, 97) # Rect for page 1 tab of left toolbar
toolbar_tab2 = Rect(27, 250, 20, 98) # Rect for page 2 tab of left toolbar
toolbar_surface1 = Surface((150, 272)) # surface for page 1 of left toolbar
toolbar_surface1.fill(toolbarColour)
toolbar_surface2 = Surface((150, 272)) # surface for page 2 of left toolbar
toolbar_surface2.fill(toolbarColour)
draw.rect(screen, boxColour, (25, 148, 24, 202), 3)
draw.line(screen, boxColour, (25, 248), (49, 248), 3)
draw.rect(screen, toolbarColour, toolbar_tab1) # show that page 1 is selected
draw.rect(screen, toolbarDark, toolbar_tab2)
draw.line(screen, toolbarColour, (48, 150), (48, 246), 3)
draw.line(screen, boxColour, (48, 250), (48, 347), 3)

# right toolbar
draw.rect(screen, toolbarColour, (1050, 150, 150, 550))
draw.rect(screen, boxColour, (1048, 148, 154, 554), 3)
draw.line(screen, boxColour, (1050, 422), (1200, 422), 4)
draw.line(screen, boxColour, (1050, 540), (1200, 540), 4)

# current-colour box
colourBox = Rect(127, 437, 65, 65) # box to show selected colour
draw.rect(screen, boxColour, (125, 435, 68, 68), 3)
text_current = trebuchetFont14.render('Current', True, boxColour)
screen.blit(text_current, (61, 450))
text_colour = trebuchetFont14.render('Colour:', True, boxColour)
screen.blit(text_colour, (63, 470))

###########################################################################

# set tools and colour palette
# the value of each tool variable is equal to the index of its Rect and Border
toolRects = [] # Rect for each tool

# left toolbar page 1 and 2 (they use the same rects and borders)
pencil, eraser, brush, spray, bucket, line, rectangle, rectangle_filled, oval, oval_filled = range(10)
eyedropper, glitter, ink, marker, polygon, polygon_filled, text_tool, blur, pixelate, selection = range(10, 20)
for i in range(2):
    for j in range(161, 370, 52):
        for k in range(60, 131, 70):
            toolRects.append(Rect(k, j, 60, 41))
            draw.rect(toolbar_surface1, WHITE, (k-50, j-150, 60, 41))
            draw.rect(toolbar_surface2, WHITE, (k-50, j-150, 60, 41))
            
# right upper toolbar
earth, moon, sun, stars, astronaut, shuttle, comet, asteroids, galaxy, satellite = range(20, 30)
for i in range(161, 370, 52):
    for j in range(1060, 1131, 70):
        toolRects.append(Rect(j, i, 60, 41))
        draw.rect(screen, WHITE, (j, i, 60, 41))
        
# right middle toolbar
undo, clear, load, save = range(30, 34)
for i in range(435, 488, 52):
    for j in range(1060, 1131, 70):
        toolRects.append(Rect(j, i, 60, 41))
        draw.rect(screen, WHITE, (j, i, 60, 41))
        
# ink tool
ink_cover = Surface((1200, 675)).convert() # surface for ink tool
ink_cover.set_alpha(100)
ink_cover.set_colorkey((0, 1, 1, 0))
ink_cover.fill((0, 1, 1, 0))

# marker tool
marker_cover = Surface((42, 42)).convert() # surface for marker tool
marker_cover.set_alpha(5)
marker_cover.set_colorkey((0, 1, 1, 0))

# polygon tool
polygon_pts = [] # list of points for polygon tool

# filled polygon tool
polygonF_pts = [] # list of points for filled polygon tool

# text tool
text = '' # keyboard input for text tool
typing = False # for text tool, whether or not the user has clicked the canvas to start/stop typing

# selection tool
selection_pts = [] # list of points for selection tool
selected = False # for selection tool, whether or not the user selected a polygon

# undo tool
undo_back = screen.subsurface(canvasRect).copy() # current canvas (also used in some other tools)
undo_backs = [undo_back] # list of canvas surfaces

# colour palette
paletteRect = Rect(50, 530, 150, 170) # Rect for colour palette

###########################################################################

# upload and blit text and images
# logo
logo = image.load("images/logo.png")
screen.blit(logo, (625-logo.get_width()/2, 75-logo.get_height()/2))
logoPic1 = image.load("images/logoplanet1.png")
screen.blit(transform.scale(logoPic1, (130, 130)), (1060, 10))
logoPic2 = image.load("images/logoplanet2.png")
screen.blit(transform.scale(logoPic2, (130, 130)), (60, 10))

# left toolbar page 1
pencilPic = image.load("images/pencil.png") # pencil
toolbar_surface1.blit(transform.scale(pencilPic, (30, 30)), (25, 16))
eraserPic = image.load("images/eraser.png") # eraser
toolbar_surface1.blit(transform.scale(eraserPic, (30 ,30)), (95, 16))
brushPic = image.load("images/brush.png") # brush
toolbar_surface1.blit(transform.scale(brushPic, (30, 30)), (24, 69))
sprayPic = image.load("images/spray.png") # spray
sprayPic = transform.rotate(sprayPic, -25.0)
toolbar_surface1.blit(transform.scale(sprayPic, (36, 42)), (93, 61))
bucketPic = image.load("images/bucket.png") # bucket
toolbar_surface1.blit(transform.scale(bucketPic, (30, 30)), (25, 120))
draw.line(toolbar_surface1, 0, (92, 148),(128, 122), 3) # line
draw.rect(toolbar_surface1, 0, (21, 173, 39, 29), 1) # rectangle (empty)
draw.rect(toolbar_surface1, 0, (91, 173, 39, 29)) # rectangle (filled)
draw.ellipse(toolbar_surface1, 0, (18, 225, 45, 29), 1) # oval (empty)
draw.ellipse(toolbar_surface1, 0, (88, 225, 45, 29)) # oval (filled)

# left toolbar page 2
eyedropperPic = image.load("images/eyedropper.png") # eyedropper
toolbar_surface2.blit(transform.scale(eyedropperPic, (31, 31)), (25, 16))
glitterPic = image.load("images/glitter.jpg") # glitter
toolbar_surface2.blit(transform.scale(glitterPic, (41, 41)), (89, 12))
inkPic = image.load("images/ink.jpg") # ink
toolbar_surface2.blit(transform.scale(inkPic, (55, 33)), (12, 66))
markerPic = image.load("images/marker.png") # marker
toolbar_surface2.blit(transform.scale(markerPic, (32, 32)), (94, 67))
polygonEx = [(53, 121), (27, 136), (37, 149), (50, 149), (44, 132)] # polygon (empty)
draw.polygon(toolbar_surface2, 0, polygonEx, 1) # random points were chosen as an example
polygonEx2 = [(i+70, j) for (i, j) in polygonEx] # polygon (filled)
draw.polygon(toolbar_surface2, 0, polygonEx2)
toolbar_surface2.blit(timesFont30.render('T', True, (0, 0, 0)), (30, 170)) # text tool -- just a 'T'
blurPic = image.load("images/blur.png") # blur tool
toolbar_surface2.blit(transform.scale(blurPic, (36, 36)), (92, 169))
pixelatePic = image.load("images/pixelate.png") # pixelate tool
toolbar_surface2.blit(transform.scale(pixelatePic, (30, 30)), (25, 224))
selectionPic = image.load("images/selection.jpg") # selection tool
toolbar_surface2.blit(transform.scale(selectionPic, (30, 30)), (95, 224))

# right upper toolbar (stamps)
earthPic = image.load("images/earth.png") # earth
stamp_earth = transform.scale(earthPic, (90, 90))
screen.blit(transform.scale(earthPic, (32, 32)), (1074, 165))
moonPic = image.load("images/moon.png") # moon
stamp_moon = transform.scale(moonPic, (60, 60))
screen.blit(transform.scale(moonPic, (32, 32)), (1144, 165))
sunPic = image.load("images/sun.png") # sun
stamp_sun = transform.scale(sunPic, (150, 150))
screen.blit(transform.scale(sunPic, (38, 38)), (1071, 214))
starsPic = image.load("images/stars.png") # stars
stamp_stars = transform.scale(starsPic, (100, 100))
starsIcon = image.load("images/stars_icon.png")
screen.blit(transform.scale(starsIcon, (32, 32)), (1144, 217))
astronautPic = image.load("images/astronaut.png") # astronaut
stamp_astronaut = transform.scale(astronautPic, (90, 130))
screen.blit(transform.scale(astronautPic, (24, 36)), (1079, 266))
shuttlePic = image.load("images/shuttle.png") # shuttle
stamp_shuttle = transform.scale(shuttlePic, (160, 80))
screen.blit(transform.scale(shuttlePic, (50, 25)), (1135, 272))
cometPic = image.load("images/comet.png") # comet
stamp_comet = transform.scale(cometPic, (100, 100))
screen.blit(transform.scale(cometPic, (32, 32)), (1074, 321))
asteroidsPic = image.load("images/asteroids.png") # asteroids
stamp_asteroids = transform.scale(asteroidsPic, (50, 50))
screen.blit(transform.scale(asteroidsPic, (32, 32)), (1144, 321))
galaxyPic = image.load("images/galaxy.png") # galaxy
stamp_galaxy = transform.scale(galaxyPic, (120, 120))
screen.blit(transform.scale(galaxyPic, (52, 52)), (1064, 366))
satellitePic = image.load("images/satellite.png") # satellite
stamp_satellite = transform.scale(satellitePic, (100, 60))
screen.blit(transform.scale(satellitePic, (48, 31)), (1136, 373))

# right middle toolbar
undoPic = image.load("images/undo.png") # undo
screen.blit(transform.scale(undoPic, (30, 30)), (1075, 440))
clearPic = image.load("images/clear.png") # clear
screen.blit(transform.scale(clearPic, (28, 28)), (1146, 441))
loadPic = image.load("images/load.png") # load
screen.blit(transform.scale(loadPic, (32, 32)), (1075, 491))
savePic = image.load("images/save.png") # save
screen.blit(transform.scale(savePic, (28, 28)), (1147, 493))

# colour palette
palette = image.load("images/palette.jpg")
screen.blit(palette, (50, 530))

# tool descriptions
tool_names = ['Pencil',
              'Eraser',
              'Paintbrush',
              'Airbrush',
              'Paint Bucket',
              'Line Tool',
              'Rectangle Tool',
              'Filled Rectangle',
              'Ellipse Tool',
              'Filled Ellipse',
              'Eyedropper',
              'Glitter',
              'Ink',
              'Marker',
              'Polygon Tool',
              'Filled Polygon',
              'Text Tool',
              'Blur Tool',
              'Pixelate',
              'Selection Tool',
              'Earth Stamp',
              'Moon Stamp',
              'Sun Stamp',
              'Stars Stamp',
              'Astronaut Stamp',
              'Shuttle Stamp',
              'Comet Stamp',
              'Asteroids Stamp',
              'Galaxy Stamp',
              'Satellite Stamp',
              'Undo',
              'Clear',
              'Load',
              'Save'] # list of strings with the name of each tool -- same indices as toolRects and toolBorders
            
tool_texts = [['Click on the canvas to', 'draw thin lines.'],
              ['Click on the canvas to', 'erase work that was', 'done.'],
              ['Click on the canvas to', 'draw thick lines.'],
              ['Click on the canvas to', 'get a spray paint', 'effect.'],
              ['Click on the canvas to', 'fill an area with the', 'given colour.'],
              ['Click and drag on the', 'canvas to draw', 'straight lines.'],
              ['Click and drag on the', 'canvas to draw', 'rectangles.'],
              ['Click and drag on the', 'canvas to draw', 'filled rectangles.'],
              ['Click and drag on the', 'canvas to draw', 'ellipses.'],
              ['Click and drag on the', 'canvas to draw', 'filled ellipses.'],
              ['Click on the canvas to', 'get the colour at the', 'mouse position.'],
              ['Click on the canvas to', 'get a glitter effect.'],
              ['Click on the canvas to', 'draw. Gets darker', 'each time you click', 'and go over it.'],
              ['Click on the canvas to', 'draw. Gets darker', 'the longer you keep', 'the mouse pressed.'],
              ['Click on the canvas to', 'select points. Click on', 'the first vertex again', 'to close the polygon.'],
              ['Click on the canvas to', 'select points. Click on', 'the first vertex again', 'to close the polygon.'],
              ['Click on the canvas to', 'start typing. Click', 'again to place the', 'text.'],
              ['Click on the canvas to', 'blur work that was', 'done.'],
              ['Click on the canvas to', 'turn work that was', 'done into pixel art.'],
              ['Click points on the', 'canvas to cut out a', 'polygon. Click again', 'to place it.'],
              ['Click on the canvas to', 'draw.'],
              ['Click on the canvas to', 'draw.'],
              ['Click on the canvas to', 'draw.'],
              ['Click on the canvas to', 'draw.'],
              ['Click on the canvas to', 'draw.'],
              ['Click on the canvas to', 'draw.'],
              ['Click on the canvas to', 'draw.'],
              ['Click on the canvas to', 'draw.'],
              ['Click on the canvas to', 'draw.'],
              ['Click on the canvas to', 'draw.'],
              ['Undo the last edit', 'made.'],
              ['Clear the canvas and', 'start over.'],
              ['Load a canvas from a', 'bitmap file.'],
              ['Save the canvas to a', 'bitmap file.']]
            # list of lists of strings with descriptions of each tool ('\n' doesn't work when blitting text) -- same indices

textRect = Rect(1050, 543, 150, 125) # will cover previous description         
text_locations = [(1060, 580), (1060, 595), (1060, 610), (1060, 625)] # where to blit each line of text

###########################################################################

# set default tools
tool = pencil # selected tool
oldtool = pencil # will go back to previous tool when the user is done with undo, clear, load, or save
tools_shown = list(range(10)) + list(range(20, 34)) # tools that are currently displayed on screen

# show left toolbar page 1
screen.blit(toolbar_surface1, (50, 150))

# draw boxes around tools
for i in tools_shown:
    if tool == i:
        borderColour = (0, 225, 0) # green box around selected tool
    else:
        borderColour = boxColour # regular box otherwise
    draw.rect(screen, borderColour, toolRects[i], 3)
    
# show description of tool
draw.rect(screen, toolbarColour, textRect)
title = titleFont.render(tool_names[tool], True, BLACK)
screen.blit(title, (1125-(title.get_width()+1)//2, 555))
for i in range(len(tool_texts[tool])):
    description = descriptionFont.render(tool_texts[tool][i], True, BLACK)
    screen.blit(description, text_locations[i])
    
# colour for drawing
drawColour = BLACK # selected colour
draw.rect(screen, drawColour, colourBox) # update current colour box

# other variables
oldx, oldy = 0, 0 # for straight line function
startx, starty = 0, 0 # for line, rectangle, and oval tools
pressL = False # whether or not the user clicked on left mouse button
releaseL = False # whether or not the user released the left mouse button

###########################################################################

running = True

while running:
    mx, my = mouse.get_pos() # the position of the mouse on the screen
    mb = mouse.get_pressed() # the state of the mouse buttons
    
    for evt in event.get():
        if evt.type == QUIT:
            running = False
            
        if evt.type == MOUSEBUTTONUP:
            if evt.button == 1:
                releaseL = True

        if evt.type == MOUSEBUTTONDOWN:
            if evt.button == 1:
                pressL = True
                startx, starty = mx, my

        if evt.type == KEYDOWN:
            if tool == text_tool and typing: # record keyboard input for text tool
                try:
                    if evt.key == K_BACKSPACE:
                        text = text[:-1]
                    elif evt.key in [K_ESCAPE, K_TAB, K_RETURN, K_UP, K_DOWN, K_LEFT, K_RIGHT]:
                        continue
                    else:
                        text += evt.unicode
                except:
                    pass
    
    if canvasRect.collidepoint(mx, my): # only draw when mouse is on the canvas
        screen.set_clip(canvasRect)

        if tool == pencil:
            if mb[0] == 1:
                for i in line_points(oldx, oldy, mx, my):
                    draw.circle(screen, drawColour, i, 2)

        elif tool == eraser:
            if mb[0] == 1:
                for i in line_points(oldx, oldy, mx, my):
                    draw.circle(screen, (255, 255, 255), i, 20)

        if tool == brush:
            if mb[0] == 1:
                for i in line_points(oldx, oldy, mx, my):
                    draw.circle(screen, drawColour, i, 20)

        elif tool == spray:
            if mb[0] == 1:
                for i in line_points(oldx, oldy, mx, my):
                    spray_paint(i[0], i[1], 20, drawColour)

        elif tool == bucket:
            if releaseL:
                bucket_fill(mx, my, screen.get_at((mx, my)), drawColour, screen)

        elif tool == line:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                for i in line_points(startx, starty, mx, my):
                    draw.circle(screen, drawColour, i, 2)
                
        elif tool == rectangle:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                minx, miny = min(startx, mx), min(starty, my)
                posw, posh = max(abs(mx-startx), 1), max(abs(my-starty), 1) # positive width and height of rectangle
                rectangle_surface = Surface((posw, posh)) # surface for rectangle tool (unfilled)
                rectangle_surface.fill(drawColour)
                rectangle_surface.set_colorkey((1, 1, 1, 0))
                if posw >= 7 and posh >= 7:
                    draw.rect(rectangle_surface, (1, 1, 1, 0), (3, 3, posw-6, posh-6))
                screen.blit(rectangle_surface, (minx, miny))

        elif tool == rectangle_filled:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                drawRect = Rect(startx, starty, mx-startx, my-starty)
                drawRect.normalize()
                draw.rect(screen, drawColour, drawRect)

        elif tool == oval:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                minx, miny = min(startx, mx), min(starty, my)
                radx, rady = max(abs(mx-startx), 1), max(abs(my-starty), 1) # dimensions of ellipse
                ellipse_surface = Surface((radx, rady)) # surface for oval tool (unfilled)
                ellipse_surface.set_colorkey((1, 1, 1, 0))
                ellipse_surface.fill((1, 1, 1, 0))
                draw.ellipse(ellipse_surface, drawColour, (0, 0, radx, rady))
                if radx >= 10 and rady >= 10:
                    draw.ellipse(ellipse_surface, (1, 1, 1, 0), (3, 3, radx-6, rady-6))
                screen.blit(ellipse_surface, (minx, miny))

        elif tool == oval_filled:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                radx, rady = max(abs(mx-startx), 1), max(abs(my-starty), 1) # dimensions of ellipse
                draw.ellipse(screen, drawColour, (min(mx, startx), min(my, starty), radx, rady))

        elif tool == eyedropper:
            if mb[0] == 1:
                drawColour = screen.get_at((mx, my))

        elif tool == glitter:
            if mb[0] == 1:
                for i in line_points(oldx, oldy, mx, my):
                    glitter_pt(i[0], i[1], 20, drawColour)

        elif tool == ink:
            if mb[0]==1:
                for i in line_points(oldx, oldy, mx, my):
                    draw.circle(ink_cover, drawColour, (i[0]-250, i[1]-150), 20)
                screen.blit(undo_back, (250, 150))
                screen.blit(ink_cover, (250, 150))
            else:
                ink_cover.fill((0, 1, 1, 0))
                
        elif tool == marker:
            if mb[0] == 1:
                marker_cover.fill((0, 1, 1, 0))
                draw.circle(marker_cover, drawColour, (21, 21), 20)
                for i in line_points(oldx, oldy, mx, my):
                    screen.blit(marker_cover, (i[0]-21, i[1]-21))

        elif tool == polygon:
            if pressL:
                if len(polygon_pts) > 0 and hypot(polygon_pts[0][0]-mx, polygon_pts[0][1]-my) < 5: # they don't have to click
                                                                                                  # on the exact same pixel
                    screen.blit(undo_back, (250, 150))
                    if len(polygon_pts) > 1:
                        draw.polygon(screen, drawColour, polygon_pts, 3)
                    else:
                        draw.circle(screen, drawColour, polygon_pts[0], 2)
                    undo_backs.append(undo_back)
                    undo_back = screen.subsurface(canvasRect).copy()
                    polygon_pts = []
                else:
                    polygon_pts.append((mx, my))
            elif len(polygon_pts) > 0:
                screen.blit(undo_back, (250, 150))
                incomplete_polygon(polygon_pts + [(mx, my)], drawColour)

        elif tool == polygon_filled: # same as the empty polygon, but with thickness 0
            if pressL:
                if len(polygonF_pts) > 0 and hypot(polygonF_pts[0][0]-mx, polygonF_pts[0][1]-my) < 5: # they don't have to click
                                                                                                     # on the exact same pixel
                    screen.blit(undo_back, (250, 150))
                    if len(polygonF_pts) > 2: # filled polygon requires at least 3 points
                        draw.polygon(screen, drawColour, polygonF_pts)
                    elif len(polygonF_pts) == 2: # regular polygon requires at least 2 points
                        draw.polygon(screen, drawColour, polygonF_pts, 3)
                    else:
                        draw.circle(screen,drawColour, polygonF_pts[0], 2)
                    undo_backs.append(undo_back)
                    undo_back = screen.subsurface(canvasRect).copy()
                    polygonF_pts = []
                else:
                    polygonF_pts.append((mx, my))
            elif len(polygonF_pts) > 0:
                screen.blit(undo_back, (250, 150))
                incomplete_polygon(polygonF_pts + [(mx, my)], drawColour)

        elif tool == text_tool: # get keyboard input in evt loop ^
            if pressL:
                if typing == False: # click to start typing
                    text = ''
                    typing = True
                else: # click again to stop typing
                    undo_backs.append(undo_back)
                    undo_back = screen.subsurface(canvasRect).copy()
                    text = ''
                    typing = False
            if typing:
                screen.blit(undo_back, (250, 150))
                textPic = texttoolFont.render(text, True, drawColour)
                w, h = textPic.get_size()
                screen.blit(textPic, (mx-w//2, my-h//2))

        elif tool == blur:
            if mb[0] == 1:
                blur_circ(mx, my, canvasRect)

        elif tool == pixelate:
            if mb[0] == 1:
                for i in range(mx-10, mx+11, 5):
                    for j in range(my-10, my+11, 5):
                        pixel(i, j, canvasRect)

        elif tool == selection:
            if selected:
                screen.blit(undo_back, (250, 150))
                draw.polygon(screen, WHITE, selection_pts)
                w, h = select_surface.get_size()
                screen.blit(select_surface, (mx-w//2, my-h//2))
                if pressL:
                    selected = False
                    undo_backs.append(undo_back)
                    undo_back = screen.subsurface(canvasRect).copy()
                    selection_pts = []
            else:
                if len(selection_pts) == 0: # make sure selected polygon is visible
                    mbColour = screen.get_at((mx, my))
                    mbAverage = (mbColour.r + mbColour.g + mbColour.b) // 3
                    if mbAverage <= 50: # white if dark area is selected
                        selectColour = WHITE
                    else: # black if light area is selected
                        selectColour = BLACK
                if pressL:
                    if len(selection_pts) > 0 and hypot(selection_pts[0][0]-mx, selection_pts[0][1]-my) < 5: # they don't have to click
                                                                                                            # on the exact same pixel
                        screen.blit(undo_back, (250, 150))
                        if len(selection_pts) > 2:
                            select_surface = cutout(selection_pts)
                            selected = True
                        else:
                            selection_pts = []
                    else:
                        selection_pts.append((mx, my))
                elif len(selection_pts) > 0:
                    screen.blit(undo_back, (250, 150))
                    incomplete_polygon(selection_pts + [(mx, my)], selectColour)

        elif tool == earth:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                screen.blit(stamp_earth, (mx-45, my-45))

        elif tool == moon:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                screen.blit(stamp_moon, (mx-30, my-30))

        elif tool == sun:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                screen.blit(stamp_sun, (mx-75, my-75))

        elif tool == stars:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                screen.blit(stamp_stars, (mx-50, my-50))

        elif tool == astronaut:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                screen.blit(stamp_astronaut, (mx-45, my-65))

        elif tool == shuttle:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                screen.blit(stamp_shuttle, (mx-80, my-40))

        elif tool == comet:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                screen.blit(stamp_comet, (mx-50, my-50))

        elif tool == asteroids:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                screen.blit(stamp_asteroids, (mx-25, my-25))

        elif tool == galaxy:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                screen.blit(stamp_galaxy, (mx-60, my-60))

        elif tool == satellite:
            if mb[0] == 1:
                screen.blit(undo_back, (250, 150))
                screen.blit(stamp_satellite, (mx-50, my-30))

        if releaseL and tool not in [eyedropper, polygon, polygon_filled, text_tool, selection]: # check if should append to undo list
                                            # don't append for eyedropper
                                            # append for polygon, filled polygon, text, and selection tools seperately
            undo_backs.append(undo_back)
            undo_back = screen.subsurface(canvasRect).copy()
            releaseL = False

    else:
        # check if colour palette is selected
        if paletteRect.collidepoint(mx, my) and mb[0] == 1:
            drawColour = screen.get_at((mx, my))

        # check if toolbar page is selected
        if toolbar_tab1.collidepoint(mx, my) and mb[0] == 1:
            draw.rect(screen, toolbarColour, toolbar_tab1) # show that page 1 is selected
            draw.rect(screen, toolbarDark, toolbar_tab2)
            draw.line(screen, toolbarColour, (48, 150), (48, 246), 3)
            draw.line(screen, boxColour, (48, 250), (48, 347), 3)
            tools_shown[:10] = list(range(10)) # replace second page with first page
            screen.blit(toolbar_surface1, (50, 150))
        elif toolbar_tab2.collidepoint(mx, my) and mb[0] == 1:
            draw.rect(screen, toolbarDark, toolbar_tab1) # show that page 1 is selected
            draw.rect(screen, toolbarColour, toolbar_tab2)
            draw.line(screen, boxColour, (48, 150), (48, 246), 3)
            draw.line(screen, toolbarColour, (48, 250), (48, 347), 3)
            tools_shown[:10] = list(range(10, 20)) # replace first page with second page
            screen.blit(toolbar_surface2, (50, 150))

        # check if a tool is selected or hovered over
        # also show tool description
        draw.rect(screen, toolbarColour, textRect)
        title = titleFont.render(tool_names[tool], True, BLACK)
        screen.blit(title, (1125-(title.get_width()+1)//2, 555))
        for i in range(len(tool_texts[tool])):
            description = descriptionFont.render(tool_texts[tool][i], True, BLACK)
            screen.blit(description, text_locations[i])
        for i in tools_shown:
            if tool == i:
                borderColour = (0, 225, 0) # green box around selected tool
            elif toolRects[i].collidepoint(mx, my):
                if mb[0] == 1:
                    tool = i
                borderColour = (255, 188, 188) # pink box and description when hover over tool
                draw.rect(screen, toolbarColour, textRect)
                title = titleFont.render(tool_names[i], True, BLACK)
                screen.blit(title, (1125-(title.get_width()+1)//2, 555))
                for j in range(len(tool_texts[i])):
                    description = descriptionFont.render(tool_texts[i][j], True, BLACK)
                    screen.blit(description, text_locations[j])
            else:
                borderColour = boxColour # regular box if not selected or hovered over
            draw.rect(screen, borderColour, toolRects[i], 3)                   

        # check if undo, clear, load, or save is selected (mouse will not be on the canvas)
        if tool in range(30, 34):
            if tool == undo:
                if releaseL: # undo only once
                    undo_back = undo_backs[-1]
                    if len(undo_backs) > 1:
                        screen.blit(undo_backs.pop(), (250, 150))
                    else:
                        screen.blit(undo_backs[0], (250, 150))
                    tool = oldtool

            elif tool == clear:
                if releaseL: # screen is only cleared once
                    draw.rect(screen, WHITE, canvasRect)
                    undo_backs.append(undo_back)
                    undo_back = screen.subsurface(canvasRect).copy()
                    tool = oldtool

            elif tool == load:
                if releaseL:
                    screen.set_clip(250, 150, 750, 550) # an image larger than the canvas might be uploaded
                    result = filedialog.askopenfilename()
                    try:
                        upload = image.load(result)
                        screen.blit(upload, (250, 150))
                        undo_backs.append(undo_back)
                        undo_back = screen.subsurface(canvasRect).copy()
                    except:
                        pass
                    tool = oldtool

            elif tool == save:
                if releaseL:
                    result = filedialog.asksaveasfilename()
                    if result:
                        image.save(screen.subsurface(canvasRect), result + '.png')
                    tool = oldtool

        else:
            oldtool = tool

    screen.set_clip(0, 0, 1250, 750)

    # the following tools need to be reset if a new tool was chosen
    if tool != polygon:
        polygon_pts = []
    if tool != polygon_filled:
        polygonF_pts = []
    if tool != text_tool:
        text = ''
        typing = False
    if tool != selection:
        selection_pts = []
        selected = False

    # update current-colour box
    draw.rect(screen, drawColour, colourBox)

    # erase previous and display new mx, my
    draw.rect(screen, toolbarColour, (1050, 670, 150, 25))
    text_mx = trebuchetFont14.render('mx: %4i' % mx, True, BLACK)
    screen.blit(text_mx, (1060, 670))
    text_my = trebuchetFont14.render('my: %3i' % my, True, BLACK)
    screen.blit(text_my, (1130, 670))

    oldx, oldy = mx, my
    pressL = False
    releaseL = False
    display_text = False
    
    display.flip()
    
quit()
