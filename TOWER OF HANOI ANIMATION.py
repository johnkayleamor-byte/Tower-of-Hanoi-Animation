import turtle
import time
import math
import tkinter as tk
import tkinter.font as tkfont  

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


    poly = [(-py, px) for px, py in poly]
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
CODE_STEP_MS = 800

screen = turtle.Screen()
screen.setup(SCREEN_WIDTH, SCREEN_HEIGHT)
screen.title("Tower of Hanoi")
screen.bgcolor("#1a1a1a")
screen.tracer(0)
screen.delay(10)

RODS = {"A": -250, "B": 0, "C": 250}

rods_state = {"A": [], "B": [], "C": []}
pending_steps = []
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

CODE_LINES = [
    "def hanoi(n, source, target, auxiliary):",
    "   if n == 0:",
    "       return",
    "   hanoi(n - 1, source, auxiliary, target)",
    "   move_disk(n, source, target)",
    "   hanoi(n - 1, auxiliary, target, source)",
    ]

CODE_FONT = ("Courier New", 11)
HEADER_FONT = ("Arial", 11, "bold")

LINE_H = 20
FIRST_LINE_Y = -232          # turtle-y of the first code line's center
PANEL_TOP = -195
PANEL_BOTTOM = FIRST_LINE_Y - (len(CODE_LINES) - 1) * LINE_H - LINE_H // 2 - 8
INFO_CHARS = 40            
PANEL_GAP = 20
PANEL_PAD = 32             


def measure_char_width():
    # measure with the SAME canvas/font that draws the text, so it always fits
    canvas = screen.getcanvas()
    probe = canvas.create_text(0, 0, text="0" * 100, font=CODE_FONT, anchor="nw")
    x1, _, x2, _ = canvas.bbox(probe)
    canvas.delete(probe)
    return (x2 - x1) / 100.0


CHAR_W = measure_char_width()
CODE_W = PANEL_PAD + max(len(line) for line in CODE_LINES) * CHAR_W
INFO_W = PANEL_PAD + INFO_CHARS * CHAR_W
CODE_LEFT = -(CODE_W + PANEL_GAP + INFO_W) / 2   
CODE_RIGHT = CODE_LEFT + CODE_W
INFO_LEFT = CODE_RIGHT + PANEL_GAP
INFO_RIGHT = INFO_LEFT + INFO_W

code_highlight = None
code_text_ids = []
call_text_id = None
depth_text_id = None
step_text_id = None

def code_line_y(index):
    return FIRST_LINE_Y - index * LINE_H

def build_code_panel():
    global code_highlight, call_text_id, depth_text_id, step_text_id
    canvas = screen.getcanvas()

    canvas.create_rectangle(CODE_LEFT, -PANEL_TOP, CODE_RIGHT, -PANEL_BOTTOM,
                            fill = "#252525", outline="#444444")
    canvas.create_rectangle(INFO_LEFT, -PANEL_TOP, INFO_RIGHT, -PANEL_BOTTOM,
                            fill="#252525", outline="#444444"
                            )
    #header
    canvas.create_text(CODE_LEFT + 16, -(PANEL_TOP - 14), text="Recursive Logic",
                       fill="white", font=HEADER_FONT, anchor = "w")
    canvas.create_text(INFO_LEFT + 16, -(PANEL_TOP - 14), text="Current Call",
                       fill="white", font=HEADER_FONT, anchor="w")

    code_highlight = canvas.create_rectangle(0, 0, 0, 0, fill="#ffe066", outline="", state="hidden")

    code_text_ids.clear()

    for i, line in enumerate(CODE_LINES):
        tid = canvas.create_text(CODE_LEFT + 16, -code_line_y(i), text=line, fill="#d0d0d0", font=CODE_FONT, anchor="w")
        code_text_ids.append(tid)

    call_text_id = canvas.create_text(INFO_LEFT + 16, -code_line_y(0), text="",
                                      fill="#8ecae6", font=CODE_FONT, anchor="w")
    depth_text_id = canvas.create_text(INFO_LEFT + 16, -code_line_y(1), text="",
                                       fill="white", font=CODE_FONT, anchor="w")
    step_text_id = canvas.create_text(INFO_LEFT + 16, -code_line_y(2), text="",
                                      fill="#ffe066", font=CODE_FONT, anchor="w")

def reset_code_panel():
    canvas = screen.getcanvas()
    canvas.itemconfig(code_highlight, state="hidden")
    for tid in code_text_ids:
        canvas.itemconfig(tid, fill="#d0d0d0")
    canvas.itemconfig(call_text_id, text="Ready")
    canvas.itemconfig(depth_text_id, text="")
    canvas.itemconfig(step_text_id, text="")


def show_step(line, n, source, target, aux, depth, text):
    canvas = screen.getcanvas()
    y = code_line_y(line)

    canvas.coords(code_highlight,
                  CODE_LEFT + 6, -y - LINE_H / 2,
                  CODE_RIGHT - 6, -y + LINE_H / 2)
    canvas.itemconfig(code_highlight, state="normal")

    for i, tid in enumerate(code_text_ids):
        canvas.itemconfig(tid, fill="#1a1a1a" if i == line else "#d0d0d0")

    canvas.itemconfig(call_text_id,
                      text=f"hanoi(n={n}, source={source}, target={target}, aux={aux})")
    canvas.itemconfig(depth_text_id, text=f"Recursion depth: {depth}")
    canvas.itemconfig(step_text_id, text=text)


def show_finished_panel():
    canvas = screen.getcanvas()
    canvas.itemconfig(code_highlight, state="hidden")
    for tid in code_text_ids:
        canvas.itemconfig(tid, fill="#d0d0d0")
    canvas.itemconfig(call_text_id, text="hanoi() finished")
    canvas.itemconfig(depth_text_id, text="")
    canvas.itemconfig(step_text_id, text=f"Solved in {move_count} moves")

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
    move_drawer.goto(0, 300)
    move_drawer.write(f"Disk {disk_number}: Rod {from_rod} → Rod {to_rod}", align="center", font=("Arial", 16, "bold"))


def show_complete_message():
    complete_drawer.clear()
    complete_drawer.penup()
    complete_drawer.goto(0, 300)
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

    canvas_x = d.xcor()
    canvas_y = -d.ycor()

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
    screen.update()
    for d in all_active_turtles:
        update_label(d)
    screen.getcanvas().update_idletasks()


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

        disk_width = 30 + i * 14
        shape_id = f"disk_{i}"
        get_rounded_poly(shape_id, disk_width)
        disk.shape(shape_id)
        disk.shapesize(1, 1)

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


def event_to_turtle_coords(event):
    canvas = screen.getcanvas()
    return canvas.canvasx(event.x), -canvas.canvasy(event.y)

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
    x, y = event_to_turtle_coords(event)

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


def plan_moves(n, source, target, auxiliary, depth=0):
    """Mirrors the recursive algorithm and records one step per line of code.
    kind = "trace" (just highlight a line) or "move" (highlight + animate a disk).
    The line numbers match CODE_LINES."""

    def add(kind, line, text):
        pending_steps.append((kind, line, n, source, target, auxiliary, depth, text))

    add("trace", 0, f"Enter hanoi({n}, {source}, {target}, {auxiliary})")

    if n == 0:
        add("trace", 1, "n == 0 is True")
        add("trace", 2, "Base case -> return")
        return

    add("trace", 1, f"n == {n}, not 0 -> keep going")

    add("trace", 3, f"Recurse -> hanoi({n-1}, {source}, {auxiliary}, {target})")
    plan_moves(n - 1, source, auxiliary, target, depth + 1)

    add("move", 4, f"Move disk {n}: {source} -> {target}")

    add("trace", 5, f"Recurse -> hanoi({n-1}, {auxiliary}, {target}, {source})")
    plan_moves(n - 1, auxiliary, target, source, depth + 1)


def start_next_move(callback_id=None):
    global anim_disk, anim_phase, anim_to_rod, anim_target_x, anim_target_y

    if callback_id is not None and callback_id != run_id:
        return

    if not is_running or puzzle_complete:
        return

    if anim_disk is not None:
        return

    if is_paused:
        screen.ontimer(lambda rid=run_id: start_next_move(rid), TICK_MS)
        return

    if not pending_steps:
        finish_puzzle()
        return

    kind, line, n, source, target, aux, depth, text = pending_steps.pop(0)
    show_step(line, n, source, target, aux, depth, text)

    if kind == "trace":
        # just show the highlighted line for a moment, then continue
        screen.ontimer(lambda rid=run_id: start_next_move(rid), CODE_STEP_MS)
        return

    from_rod, to_rod = source, target

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

    refresh_screen()

    if anim_phase is None:
        rods_state[anim_to_rod].append(d)
        anim_disk = None
        move_count += 1
        update_score_display()

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
    show_finished_panel()
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

    pending_steps.clear()
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
    reset_code_panel()

    build_disks()
    draw_buttons()
    update_score_display()

    pending_steps.clear()

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
    x, y = event_to_turtle_coords(event)

    if 140 <= x <= 245 and 245 <= y <= 280:
        toggle_pause()
    elif 260 <= x <= 365 and 245 <= y <= 280:
        open_restart_window()


screen.getcanvas().bind("<Button-1>", handle_click)

is_running = True

draw_rods()
draw_buttons()
build_code_panel()
reset_code_panel()
build_disks()
update_score_display()

plan_moves(NUM_DISKS, "A", "C", "B")

screen.ontimer(lambda: start_next_move(run_id), 500)
screen.ontimer(label_heartbeat, 100)

import traceback

def show_error_in_window(exc, val, tb):
    traceback.print_exception(exc, val, tb)
    try:
        line = traceback.extract_tb(tb)[-1].lineno
        canvas = screen.getcanvas()
        canvas.itemconfig(call_text_id, text=f"ERROR at line {line}", fill="#ff6b6b")
        canvas.itemconfig(depth_text_id, text=exc.__name__, fill="#ff6b6b")
        canvas.itemconfig(step_text_id, text=str(val)[:40], fill="#ff6b6b")
    except Exception:
        pass

screen.getcanvas().winfo_toplevel().report_callback_exception = show_error_in_window

screen.mainloop()