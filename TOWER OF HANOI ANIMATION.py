import turtle
import time
import math

def get_rounded_poly(shape_name, target_width):
    h = 30
    r = 10
    w = target_width
    poly = []

    for angle in range(0, 91, 15):
        rad = math.radians(angle)
        poly.append((w/2 - r + r*math.sin(rad), -h/2 + r - r*math.cos(rad)))

    for angle in range(0, 91, 15):
            rad = math.radians(angle)
            poly.append((w/2 - r + r*math.cos(rad), h/2 - r + r*math.sin(rad)))

    for angle in range(0, 91, 15):
            rad = math.radians(angle)
            poly.append((-w/2 + r - r*math.sin(rad), h/2 - r + r*math.cos(rad)))

    for angle in range(0, 91, 15):
            rad = math.radians(angle)
            poly.append((-w/2 + r - r*math.cos(rad), -h/2 + r - r*math.sin(rad)))

    turtle.register_shape(shape_name, tuple(poly))

#Global Set Up
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
NUM_DISKS = 4 

GROUND_LEVEL = -150
BASE_WIDTH = 80
ROD_HEIGHT = 330
PEAK_HEIGHT = GROUND_LEVEL + ROD_HEIGHT + 40

GLIDE_STEP = 12
TICK_MS = 12
PAUSE_BETWEEN_MOVES = 120

screen = turtle.Screen()
screen.setup(SCREEN_WIDTH, SCREEN_HEIGHT)
screen.title("Tower of Hanoi")
screen.bgcolor("#1a1a1a")
screen.tracer(0)
screen.delay(10)

#Rod X-coordinates
RODS = {"A": -250, "B": 0, "C": 250}
#Dictionary to store the disk on each rod
rods_state = {"A": [], "B": [], "C": []}
pending_moves = []
is_running = False
move_count = 0
button_hovered = False

#Creating the environment 
drawer = turtle.Turtle()
drawer.hideturtle()
drawer.speed(0)

button_drawer = turtle.Turtle()
button_drawer.hideturtle()
button_drawer.speed(0)

counter_drawer = turtle.Turtle()
counter_drawer.hideturtle()
counter_drawer.speed(0)
counter_drawer.color("white")

move_drawer = turtle.Turtle()
move_drawer.hideturtle()
move_drawer.speed(0)
move_drawer.color("white")

def update_score_display():
     #wipes old score and render the fresh move count
    counter_drawer.clear()
    counter_drawer.penup()
    counter_drawer.goto(-350, 250)
    counter_drawer.write(f"Moves: {move_count}", align="left", font=("Arial", 16, "bold"))
    screen.update()

def update_move_display(disk_number, from_rod, to_rod):
     move_drawer.clear()
     move_drawer.penup()
     move_drawer.goto(0, -300)

     move_drawer.write(f"Disk {disk_number}: Rod {from_rod} → Rod {to_rod}", align="center", font=("Arial", 16, "bold"))

def draw_rods():
    
    drawer.clear()
    drawer.color("white")
    drawer.pensize(5)

    for name, x in RODS.items():
          drawer.penup()
          drawer.goto(x - BASE_WIDTH, GROUND_LEVEL)
          drawer.pendown()
          drawer.goto(x + BASE_WIDTH, GROUND_LEVEL)

          drawer.penup()
          drawer.goto(x, GROUND_LEVEL)
          drawer.pendown()
          drawer.goto(x, GROUND_LEVEL + 250)

def draw_button():
   
    button_drawer.clear()
    button_drawer.penup()
    button_drawer.goto(260, 245)
    button_drawer.pendown()
    if button_hovered:
        button_drawer.color("#ffe066")
    else:
        button_drawer.color("#ffca3a")
    button_drawer.begin_fill()

    for _ in range(2):
            button_drawer.forward(100)
            button_drawer.left(90)
            button_drawer.forward(35)
            button_drawer.left(90)
    button_drawer.end_fill()         

    button_drawer.penup()
    button_drawer.color("white")
    button_drawer.goto(310, 255)
    button_drawer.write("RESTART", align="center", font=("Arial", 10, "bold"))

     #render the initial score
    update_score_display()
    
all_active_turtles = []
disk_labels = []

def update_label(d):
    d.label.clear()
    d.label.goto(d.xcor(), d.ycor() - 7)
    d.label.write(d.label_text, align="center", font=("Arial", 12, "bold"))

def redraw_all_labels():
     for d in all_active_turtles:
        update_label(d)

def refresh_screen():
     screen.update()
     redraw_all_labels()

def label_heartbeat():
     refresh_screen()
     screen.ontimer(label_heartbeat, 150)

def build_disks():
    #wipes old graphics and spawns
    global all_active_turtles, disk_labels
    for t in all_active_turtles:
         t.hideturtle()
         t.clear()

    for label in disk_labels:
         label.hideturtle()
         label.clear()

    all_active_turtles.clear()
    disk_labels.clear()

    rods_state["A"].clear()
    rods_state["B"].clear()
    rods_state["C"].clear()


    #Creating the disk
    colors = ["#ff595e", "#ffca3a", "#8ac926", "#1982c4", "#6a4c93", "#00b4d8", "#f72585", "#9d4edd"]

    for i in range(NUM_DISKS, 0, -1):
        disk = turtle.Turtle()
        disk.penup()
        disk.speed(0)

        disk_width = 40 + (NUM_DISKS - i)
        shape_id = f"disk_{i}"

        get_rounded_poly(shape_id, disk_width)
        disk.shape(shape_id)
        disk.shapesize(stretch_wid=1, stretch_len=i * 0.8)

        color_index = (i - 1) % len(colors)
        disk.color("black", colors[color_index])

        y_pos = (GROUND_LEVEL + 19) + (len(rods_state["A"]) * 34)
        disk.goto(RODS["A"], y_pos)

        label = turtle.Turtle()
        label.hideturtle()
        label.penup()
        label.color("white")
        label.label_text = str(i)
        label.goto(RODS["A"], y_pos - 7)
        label.write(label.label_text, align="center", font=("Arial", 10, "bold"))

        disk.label = label
        disk.label_text = str(i)     

        rods_state["A"].append(disk)
        all_active_turtles.append(disk)
        disk_labels.append(label)

    refresh_screen()

anim_disk = None
anim_phase = None
anim_to_rod = None
anim_target_x = 0
anim_target_y = 0

def handle_motion(event):
    global button_hovered
    x = event.x - (SCREEN_WIDTH / 2)
    y = (SCREEN_HEIGHT / 2) - event.y

    is_over_button = (260 <= x <= 360) and (245 <= y <= 280)

    if is_over_button != button_hovered:
        button_hovered = is_over_button
        draw_button()

    if button_hovered:
         screen.getcanvas().config(cursor = "hand2")
    else:
         screen.getcanvas().config(cursor = "")

def plan_moves(n, source, target, auxiliary):
    if n == 0:
          return
    plan_moves(n - 1, source, auxiliary, target)
    pending_moves.append((source, target))
    plan_moves(n - 1, auxiliary, target, source)

def start_next_move():
    global anim_disk, anim_phase, anim_to_rod, anim_target_x, anim_target_y
    if not is_running:
         return
    if not pending_moves:                
         return
    from_rod, to_rod = pending_moves.pop(0)
    if not rods_state[from_rod]:
         return
    
    anim_disk = rods_state[from_rod].pop()
    update_move_display(anim_disk.label_text, from_rod, to_rod)
    anim_to_rod = to_rod
    anim_target_x = RODS[to_rod]
    anim_target_y = (GROUND_LEVEL + 19) + (len(rods_state[to_rod]) * 34)
    anim_phase = "up"
    screen.ontimer(animation_tick, PAUSE_BETWEEN_MOVES)

def animation_tick():
    global anim_disk, anim_phase, move_count
    if not is_running or anim_disk is None:
         return
    d = anim_disk

    if anim_phase == "up":
         d.sety(min(d.ycor() + GLIDE_STEP, PEAK_HEIGHT))

         if d.ycor() >= PEAK_HEIGHT:
              anim_phase = "across"

    elif anim_phase == "across":
        if anim_target_x > d.xcor():
            d.setx(min(d.xcor() + GLIDE_STEP, anim_target_x))
        else:
            d.setx(max(d.xcor() - GLIDE_STEP, anim_target_x))

        if d.xcor() == anim_target_x:
            anim_phase = "down"

    elif anim_phase == "down":
        d.sety(max(d.ycor() - GLIDE_STEP, anim_target_y))

        if d.ycor() <= anim_target_y:
            anim_phase = None

    refresh_screen()

    if anim_phase is None:
        rods_state[anim_to_rod].append(d)
        move_count += 1
        update_score_display()
        anim_disk = None
        screen.ontimer(start_next_move, PAUSE_BETWEEN_MOVES)
    else:
        screen.ontimer(animation_tick, TICK_MS)

def handle_click(x, y):
     #Detect if the click landed inside the structure and restart box
    global NUM_DISKS, is_running, move_count, anim_disk

    if 260 <= x <= 360 and 245 <= y <= 280:

        was_running = is_running

        is_running = False

        user_input = screen.numinput("Disk Selection", "Enter number of Disk (3-8):", default=NUM_DISKS, minval=3, maxval=8)

        if user_input is None:
             is_running = was_running

             if is_running:
                  if anim_disk is not None:
                     screen.ontimer(animation_tick, TICK_MS)
                  else:
                     screen.ontimer(start_next_move, PAUSE_BETWEEN_MOVES)

             return
        
        is_running = False
        pending_moves.clear()
        anim_disk = None
             
        NUM_DISKS =int(user_input)
        move_count = 0

        draw_button()
        build_disks()
        update_score_display()

        pending_moves.clear()
        plan_moves(NUM_DISKS, "A", "C", "B")

        is_running = True
        screen.ontimer(start_next_move, 600)

screen.getcanvas().bind("<Motion>", handle_motion)
screen.onclick(handle_click)

is_running = True
draw_rods()
draw_button()
build_disks()
update_score_display()

plan_moves(NUM_DISKS, "A", "C", "B")
screen.ontimer(start_next_move, 1000)
screen.ontimer(label_heartbeat, 150)

screen.mainloop()