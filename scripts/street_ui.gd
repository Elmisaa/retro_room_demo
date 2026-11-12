extends CanvasLayer
## Интерфейс улицы, как в комнате: значки-подсказки над объектами (hotspot.gd),
## субтитр внизу и список клавиш в углу (H — скрыть).
## Значки следуют за точками hint_point.gd в мире с учётом камеры.

const HOTSPOT := preload("res://scripts/hotspot.gd")

@onready var subtitle: Control = $Subtitle
@onready var subtitle_text: Label = $Subtitle/Text
@onready var help: Label = $Help

var _pairs: Array = []   # [точка в мире, значок на экране]
var _timer := 0.0


func _ready() -> void:
	subtitle.hide()
	_build.call_deferred()


func _build() -> void:
	for p in get_tree().get_nodes_in_group("hint_points"):
		var h := Control.new()
		h.set_script(HOTSPOT)
		h.set("icon", p.icon)
		h.set("text", p.text)
		h.size = Vector2(40, 28) if p.icon == "eye" else Vector2(28, 28)
		add_child(h)
		h.activated.connect(say)
		_pairs.append([p, h])
	move_child(subtitle, -1)


func _process(delta: float) -> void:
	var cam := get_viewport().get_camera_2d()
	if cam:
		var cx: float = cam.get_meta("true_x", cam.global_position.x)
		var view_origin := Vector2(cx - 480.0, cam.global_position.y - 360.0)
		for pair in _pairs:
			var p: Node2D = pair[0]
			var h: Control = pair[1]
			h.position = (p.global_position - view_origin - h.size / 2.0).round()
	if _timer > 0.0:
		_timer -= delta
		if _timer <= 0.0:
			subtitle.hide()


func say(line: String) -> void:
	subtitle_text.text = line
	subtitle.show()
	_timer = 5.0


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_H:
		help.visible = not help.visible
