from vpython import *

# Create a sphere
ball = sphere(pos=vector(0, 0, 0), radius=0.5, color=color.red)

# Variables to manage dragging
dragging = False
drag_offset = vector(0, 0, 0)
drag_plane_normal = vector(0, 0, 1)  # will be updated on drag start
drag_plane_point = vector(0, 0, 0)

def on_mousedown(evt):
    global dragging, drag_offset, drag_plane_normal, drag_plane_point
    # Use scene.mouse.pick to get the object that was clicked
    picked = scene.mouse.pick
    if picked is ball:
        dragging = True
        # Define the drag plane to be perpendicular to the current view
        drag_plane_normal = scene.forward
        drag_plane_point = ball.pos
        # Project the mouse ray onto the drag plane
        proj = scene.mouse.project(normal=drag_plane_normal, d=dot(drag_plane_normal, drag_plane_point))
        if proj:
            drag_offset = ball.pos - proj

def on_mousemove(evt):
    if dragging:
        # Project the current mouse position onto the drag plane
        proj = scene.mouse.project(normal=drag_plane_normal, d=dot(drag_plane_normal, drag_plane_point))
        if proj:
            ball.pos = proj + drag_offset

def on_mouseup(evt):
    global dragging
    dragging = False
    scene.delete()

# Bind the event handlers.
scene.bind("mousedown", on_mousedown)
scene.bind("mousemove", on_mousemove)
scene.bind("mouseup", on_mouseup)

# Main loop to keep the program running.
while True:
    rate(60)
