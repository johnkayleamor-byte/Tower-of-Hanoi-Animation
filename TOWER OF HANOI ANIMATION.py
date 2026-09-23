import turtle
import time
import math
import tkinter as tk

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


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
NUM_DISKS = 4

GROUND_LEVEL = -150
BASE_WIDTH = 80
ROD_HEIGHT = 330
PEAK_HEIGHT = GROUND_LEVEL + ROD_HEIGHT + 40

GLIDE_STEP = 6
TICK_MS = 12
PAUSE_BETWEEN_MOVES = 100

screen = turtle.Screen()
screen.setup(SCREEN_WIDTH, SCREEN_HEIGHT)
screen.title("Tower of Hanoi")
screen.bgcolor("#1a1a1a")
screen.tracer(0)
screen.delay(10)

RODS = {"A": -250, "B": 0, "C": 250}

rods_state = {"A": [], "B": [], "C": []}
pending_moves = []
is_running = False
is_paused = False
puzzle_complete = False
move_count = 0
button_hovered = None
run_id = 0

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

complete_drawer = turtle.Turtle()
complete_drawer.hideturtle()
complete_drawer.speed(0)
complete_drawer.color("white")


def update_score_display():
    counter_drawer.clear()
    counter_drawer.penup()
    counter_drawer.goto(-350, 250)
    counter_drawer.write(f"Moves: {move_count}", align="left", font=("Arial", 16, "bold"))
    refresh_screen()


def update_move_display(disk_number, from_rod, to_rod):
    move_drawer.clear()
    move_drawer.penup()
    move_drawer.goto(0, -300)
    move_drawer.write(f"Disk {disk_number}: Rod {from_rod} → Rod {to_rod}", align="center", font=("Arial", 16, "bold"))


def show_complete_message():
    complete_drawer.clear()
    complete_drawer.penup()
    complete_drawer.goto(0, -255)
    complete_drawer.write(f"PUZZLE COMPLETE!  {move_count} moves", align="center", font=("Arial", 20, "bold"))


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

        drawer.penup()
        drawer.goto(x, GROUND_LEVEL - 25)
        drawer.write(name, align="center", font=("Arial", 14, "bold"))


def draw_button(x1, y1, x2, y2, fill_color, text, hovered):
    button_drawer.penup()
    button_drawer.goto(x1, y1)
    button_drawer.pendown()

    if hovered:
        button_drawer.color("#ffe066")
    else:
        button_drawer.color(fill_color)

    button_drawer.begin_fill()

    for _ in range(2):
        button_drawer.forward(x2 - x1)
        button_drawer.left(90)
        button_drawer.forward(y2 - y1)
        button_drawer.left(90)

    button_drawer.end_fill()

    button_drawer.penup()
    button_drawer.color("white")
    button_drawer.goto((x1 + x2) / 2, y1 + 9)
    button_drawer.write(text, align="center", font=("Arial", 10, "bold"))


def draw_buttons():
    button_drawer.clear()

    if is_paused:
        pause_text = "RESUME"
    else:
        pause_text = "PAUSE"

    draw_button(140, 245, 245, 280, "#4dabf7", pause_text, button_hovered == "pause")
    draw_button(260, 245, 365, 280, "#ffca3a", "RESTART", button_hovered == "restart")

    update_score_display()


all_active_turtles = []


def update_label(d):
    canvas = screen.getcanvas()
    
    # Exact coordinate sync dynamically fetching canvas dimensions
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    if w <= 1:
        w = SCREEN_WIDTH
    if h <= 1:
        h = SCREEN_HEIGHT

    canvas_x = d.xcor() + (w / 2)
    canvas_y = (h / 2) - d.ycor()

    if getattr(d, "label_id", None) is None:
        d.label_id = canvas.create_text(
            canvas_x,
            canvas_y,
            text=d.label_text,
            fill="white",
            font=("Arial", 11, "bold"),
            anchor="center"
        )
    else:
        canvas.coords(d.label_id, canvas_x, canvas_y)
        canvas.itemconfig(d.label_id, text=d.label_text, fill="white", font=("Arial", 11, "bold"))

    canvas.tag_raise(d.label_id)


def redraw_all_labels():
    for d in all_active_turtles:
        update_label(d)


def refresh_screen():
    for d in all_active_turtles:
        update_label(d)
    screen.update()


def label_heartbeat():
    refresh_screen()
    screen.ontimer(label_heartbeat, 100)


def build_disks():
    global all_active_turtles

    canvas = screen.getcanvas()

    for t in all_active_turtles:
        t.hideturtle()
        t.clear()
        if hasattr(t, "label_id") and t.label_id is not None:
            try:
                canvas.delete(t.label_id)
            except tk.TclError:
                pass
            t.label_id = None

    all_active_turtles.clear()
    rods_state["A"].clear()
    rods_state["B"].clear()
    rods_state["C"].clear()

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

        x_pos = RODS["A"]
        y_pos = (GROUND_LEVEL + 19) + (len(rods_state["A"]) * 34)
        disk.goto(x_pos, y_pos)
        disk.label_text = str(i)
        disk.label_id = None

        rods_state["A"].append(disk)
        all_active_turtles.append(disk)

    refresh_screen()


anim_disk = None
anim_phase = None
anim_to_rod = None
anim_target_x = 0
anim_target_y = 0


def handle_motion(event):
    global button_hovered

    canvas = screen.getcanvas()
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    if w <= 1:
        w = SCREEN_WIDTH
    if h <= 1:
        h = SCREEN_HEIGHT

    x = event.x - (w / 2)
    y = (h / 2) - event.y

    old_button = button_hovered
    button_hovered = None

    if 140 <= x <= 245 and 245 <= y <= 280:
        button_hovered = "pause"
    elif 260 <= x <= 365 and 245 <= y <= 280:
        button_hovered = "restart"

    if old_button != button_hovered:
        draw_buttons()

    if button_hovered:
        screen.getcanvas().config(cursor="hand2")
    else:
        screen.getcanvas().config(cursor="")


def plan_moves(n, source, target, auxiliary):
    if n == 0:
        return

    plan_moves(n - 1, source, auxiliary, target)
    pending_moves.append((source, target))
    plan_moves(n - 1, auxiliary, target, source)


def start_next_move(callback_id=None):
    global anim_disk, anim_phase, anim_to_rod, anim_target_x, anim_target_y

    if callback_id is not None and callback_id != run_id:
        return

    if not is_running or puzzle_complete:
        return

    if is_paused:
        screen.ontimer(lambda rid=run_id: start_next_move(rid), TICK_MS)
        return

    if not pending_moves:
        finish_puzzle()
        return

    from_rod, to_rod = pending_moves.pop(0)

    if not rods_state[from_rod]:
        finish_puzzle()
        return

    anim_disk = rods_state[from_rod].pop()

    update_move_display(anim_disk.label_text, from_rod, to_rod)

    anim_to_rod = to_rod
    anim_target_x = RODS[to_rod]
    anim_target_y = (GROUND_LEVEL + 19) + (len(rods_state[to_rod]) * 34)
    anim_phase = "up"

    current_run = run_id

    screen.ontimer(
        lambda rid=current_run: animation_tick(rid), PAUSE_BETWEEN_MOVES)


def animation_tick(callback_id=None):
    global anim_disk, anim_phase, move_count

    if callback_id is not None and callback_id != run_id:
        return

    if not is_running or anim_disk is None or puzzle_complete:
        return

    if is_paused:
        screen.ontimer(lambda rid=run_id: animation_tick(rid), TICK_MS)
        return

    d = anim_disk

    if anim_phase == "up":
        new_y = min(d.ycor() + GLIDE_STEP, PEAK_HEIGHT)
        d.sety(new_y)
        if d.ycor() >= PEAK_HEIGHT:
            anim_phase = "across"

    elif anim_phase == "across":
        step_x = GLIDE_STEP if anim_target_x > d.xcor() else -GLIDE_STEP
        new_x = d.xcor() + step_x
        if (step_x > 0 and new_x > anim_target_x) or (step_x < 0 and new_x < anim_target_x):
            new_x = anim_target_x
        d.setx(new_x)
        if d.xcor() == anim_target_x:
            anim_phase = "down"

    elif anim_phase == "down":
        new_y = max(d.ycor() - GLIDE_STEP, anim_target_y)
        d.sety(new_y)
        if d.ycor() <= anim_target_y:
            anim_phase = None

    update_label(d)
    refresh_screen()

    if anim_phase is None:
        rods_state[anim_to_rod].append(d)
        move_count += 1
        update_score_display()

        if len(rods_state["C"]) == NUM_DISKS:
            finish_puzzle()
            return

        current_run = run_id

        screen.ontimer(lambda rid=current_run: start_next_move(rid), PAUSE_BETWEEN_MOVES)
    else:
        current_run = run_id
        screen.ontimer(lambda rid=current_run: animation_tick(rid), TICK_MS)


def finish_puzzle():
    global is_running, puzzle_complete, anim_disk, anim_phase

    is_running = False
    puzzle_complete = True
    anim_disk = None
    anim_phase = None

    move_drawer.clear()
    show_complete_message()
    refresh_screen()


dialog_open = False
restart_window = None
entry = None
error_label = None


def finish_restart():
    global NUM_DISKS, is_running, is_paused, puzzle_complete
    global move_count, anim_disk, anim_phase, dialog_open
    global restart_window, run_id

    if restart_window is None:
        return

    try:
        user_input = int(entry.get())
    except (ValueError, tk.TclError):
        if error_label is not None:
            error_label.config(text="Enter a number from 3 to 8.")
        return

    if user_input < 3 or user_input > 8:
        if error_label is not None:
            error_label.config(text="Enter a number from 3 to 8.")
        return

    run_id += 1

    dialog_open = False
    is_running = False
    is_paused = False
    puzzle_complete = False

    pending_moves.clear()
    anim_disk = None
    anim_phase = None

    if restart_window is not None:
        try:
            restart_window.destroy()
        except tk.TclError:
            pass
        restart_window = None

    NUM_DISKS = int(user_input)
    move_count = 0

    move_drawer.clear()
    complete_drawer.clear()

    build_disks()
    draw_buttons()
    update_score_display()

    pending_moves.clear()

    plan_moves(NUM_DISKS, "A", "C", "B")

    is_running = True

    current_run = run_id

    screen.ontimer(
        lambda rid=current_run: start_next_move(rid),
        300
    )


def cancel_restart():
    global dialog_open, restart_window

    dialog_open = False

    if restart_window is None:
        return

    try:
        restart_window.destroy()
    except tk.TclError:
        pass

    restart_window = None
    screen.update()


def open_restart_window():
    global dialog_open, restart_window, entry, error_label

    if dialog_open:
        return

    dialog_open = True
    root = screen.getcanvas().winfo_toplevel()

    restart_window = tk.Toplevel(root)
    restart_window.title("Restart puzzle")
    restart_window.configure(bg="#252525")
    restart_window.transient(root)
    restart_window.resizable(False, False)
    restart_window.grab_set()
    restart_window.attributes("-topmost", True)

    content = tk.Frame(restart_window, bg="#252525", padx=20, pady=15)
    content.pack(fill="both")

    title_label = tk.Label(
        content,
        text="Enter number of Disk (3-8):",
        bg="#252525",
        fg="white",
        font=("Arial", 11, "bold")
    )
    title_label.pack(pady=(0, 8))

    entry = tk.Entry(
        content,
        justify="center",
        font=("Arial", 12)
    )
    entry.pack(fill="x")

    entry.insert(0, str(NUM_DISKS))
    entry.focus()

    error_label = tk.Label(
        content,
        text="",
        bg="#252525",
        fg="#ff6b6b",
        font=("Arial", 9)
    )
    error_label.pack(pady=(6, 0))

    button_frame = tk.Frame(content, bg="#252525")
    button_frame.pack(pady=10)

    ok_button = tk.Button(
        button_frame,
        text="OK",
        width=8,
        command=finish_restart
    )
    ok_button.pack(side="left", padx=5)

    cancel_button = tk.Button(
        button_frame,
        text="Cancel",
        width=8,
        command=cancel_restart
    )
    cancel_button.pack(side="left", padx=5)

    restart_window.protocol("WM_DELETE_WINDOW", cancel_restart)
    restart_window.update_idletasks()
    restart_window.geometry(f"300x{170}")
    restart_window.deiconify()


def toggle_pause():
    global is_paused
    if puzzle_complete:
        return

    is_paused = not is_paused

    draw_buttons()
    refresh_screen()


screen.getcanvas().bind("<Motion>", handle_motion)


def handle_click(event):
    canvas = screen.getcanvas()
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    if w <= 1:
        w = SCREEN_WIDTH
    if h <= 1:
        h = SCREEN_HEIGHT

    x = event.x - (w / 2)
    y = (h / 2) - event.y

    if 140 <= x <= 245 and 245 <= y <= 280:
        toggle_pause()
    elif 260 <= x <= 365 and 245 <= y <= 280:
        open_restart_window()


screen.getcanvas().bind("<Button-1>", handle_click)

is_running = True

draw_rods()
draw_buttons()
build_disks()
update_score_display()

plan_moves(NUM_DISKS, "A", "C", "B")

screen.ontimer(start_next_move, 500)
screen.ontimer(label_heartbeat, 100)

screen.mainloop()