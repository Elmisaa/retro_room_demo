extends CanvasLayer
## Меню-пауза поверх любой сцены (autoload «PauseMenu» в project.godot).
## Esc — открыть/закрыть. Пока меню открыто, игра на паузе,
## экран слегка размыт и затемнён (shaders/menu_blur.gdshader).
## ↑/↓ (или W/S) — выбор, Enter/Space — выполнить; работает и мышью.
## При запуске игры меню открыто поверх первой сцены.

const ITEMS := [
	{"title": "КОМНАТА", "scene": "res://main.tscn"},
	{"title": "УЛИЦА", "scene": "res://night_street.tscn"},
	{"title": "ВЫХОД", "scene": ""},
]
const BOX := Vector2(340, 52)
const STEP := 66.0
const FONT_SIZE := 22
const BLUR_SHADER := preload("res://shaders/menu_blur.gdshader")

const C_ON := Color(1, 1, 1, 0.95)
const C_OFF := Color(1, 1, 1, 0.4)

var selected := 0
var _screen: Control
var _font: Font


func _ready() -> void:
	layer = 100
	process_mode = Node.PROCESS_MODE_ALWAYS
	_font = ThemeDB.fallback_font

	# Размытие + затемнение всего, что под меню.
	var backdrop := ColorRect.new()
	backdrop.set_anchors_preset(Control.PRESET_FULL_RECT)
	backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mat := ShaderMaterial.new()
	mat.shader = BLUR_SHADER
	backdrop.material = mat
	add_child(backdrop)

	_screen = Control.new()
	_screen.set_anchors_preset(Control.PRESET_FULL_RECT)
	_screen.mouse_filter = Control.MOUSE_FILTER_STOP
	_screen.draw.connect(_draw_menu)
	_screen.gui_input.connect(_on_gui_input)
	add_child(_screen)

	open.call_deferred()


func is_open() -> bool:
	return visible


func open() -> void:
	visible = true
	get_tree().paused = true
	selected = _current_index()


func close() -> void:
	visible = false
	get_tree().paused = false


func _current_index() -> int:
	var cur := get_tree().current_scene
	if cur:
		for i in ITEMS.size():
			if ITEMS[i]["scene"] == cur.scene_file_path:
				return i
	return 0


func _process(_delta: float) -> void:
	if visible:
		_screen.queue_redraw()


func _item_rect(i: int) -> Rect2:
	var s := _screen.size
	var top := s.y / 2.0 - (ITEMS.size() * STEP - (STEP - BOX.y)) / 2.0
	return Rect2(Vector2((s.x - BOX.x) / 2.0, top + i * STEP), BOX)


func _unhandled_input(event: InputEvent) -> void:
	if not (event is InputEventKey and event.pressed and not event.echo):
		return
	if event.physical_keycode == KEY_ESCAPE:
		if visible:
			close()
		else:
			open()
		get_viewport().set_input_as_handled()
		return
	if not visible:
		return
	match event.physical_keycode:
		KEY_UP, KEY_W:
			selected = (selected - 1 + ITEMS.size()) % ITEMS.size()
		KEY_DOWN, KEY_S:
			selected = (selected + 1) % ITEMS.size()
		KEY_ENTER, KEY_KP_ENTER, KEY_SPACE:
			_activate(selected)
		_:
			return
	get_viewport().set_input_as_handled()


func _on_gui_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		for i in ITEMS.size():
			if _item_rect(i).has_point(event.position):
				selected = i
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		for i in ITEMS.size():
			if _item_rect(i).has_point(event.position):
				_activate(i)


func _activate(i: int) -> void:
	var scene: String = ITEMS[i]["scene"]
	if scene == "":
		get_tree().quit()
		return
	var cur := get_tree().current_scene
	if cur == null or cur.scene_file_path != scene:
		get_tree().change_scene_to_file(scene)
	close()


func _draw_menu() -> void:
	var s := _screen.size
	var first := _item_rect(0)
	_screen.draw_string(_font, Vector2(0, first.position.y - 28), "ПАУЗА",
		HORIZONTAL_ALIGNMENT_CENTER, s.x, 16, Color(1, 1, 1, 0.55))

	for i in ITEMS.size():
		var r := _item_rect(i)
		var on := i == selected
		var col := C_ON if on else C_OFF
		_screen.draw_rect(r, Color(0, 0, 0, 0.5), true)
		_screen.draw_rect(r, col, false, 1.0)
		_screen.draw_string(_font, Vector2(r.position.x, r.position.y + r.size.y / 2.0 + FONT_SIZE * 0.35),
			ITEMS[i]["title"], HORIZONTAL_ALIGNMENT_CENTER, r.size.x, FONT_SIZE, col)
