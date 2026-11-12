extends Control
## Интерактивная точка: рисует иконку (лупа или глаз) и по клику отдаёт текст.

signal activated(text: String)

@export_enum("look", "eye") var icon: String = "look"
@export_multiline var text: String = ""

var _hovered := false


func _ready() -> void:
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	mouse_entered.connect(_set_hover.bind(true))
	mouse_exited.connect(_set_hover.bind(false))


func _set_hover(value: bool) -> void:
	_hovered = value
	queue_redraw()


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		activated.emit(text)
		accept_event()


func _draw() -> void:
	var c := size / 2.0
	var col := Color(1, 1, 1, 1.0 if _hovered else 0.8)
	var w := 2.0
	if icon == "eye":
		draw_arc(c + Vector2(0, 8), 16, deg_to_rad(-150), deg_to_rad(-30), 24, col, w)
		draw_arc(c + Vector2(0, -8), 16, deg_to_rad(30), deg_to_rad(150), 24, col, w)
		draw_arc(c, 4.5, 0, TAU, 16, col, w)
		draw_circle(c, 1.5, col)
	else:
		draw_arc(c + Vector2(-2, -2), 6, 0, TAU, 20, col, w)
		draw_line(c + Vector2(2.5, 2.5), c + Vector2(8, 8), col, w)
