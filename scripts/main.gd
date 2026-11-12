extends Node2D
## Демо-сцена для проверки шейдера пост-обработки.
## Клавиши — см. подсказку в левом верхнем углу (H — скрыть).

const PIXEL_PRESETS := [Vector2(160, 120), Vector2(200, 150), Vector2(240, 180), Vector2(320, 240), Vector2(480, 360)]
const TINT_STEP := 0.1
## Пресеты цветокоррекции: [название, цвет теней, цвет светов]
const TINT_PRESETS := [
	["зелёный", Color(0.03, 0.09, 0.07), Color(0.9, 1.0, 0.95)],
	["синий", Color(0.04, 0.07, 0.18), Color(0.85, 0.92, 1.0)],
	["тёплый", Color(0.12, 0.06, 0.03), Color(1.0, 0.93, 0.82)],
]

@onready var post: ColorRect = $PostFX/Effect
@onready var subtitle: Control = $UI/Subtitle
@onready var subtitle_text: Label = $UI/Subtitle/Text
@onready var help: Label = $UI/Help
@onready var dust: Node2D = $Dust

var mat: ShaderMaterial
var pixel_idx := 3
var tint_idx := 0
var subtitle_timer := 0.0


func _ready() -> void:
	mat = post.material as ShaderMaterial
	for h in $UI/Hotspots.get_children():
		h.activated.connect(say)
	say("Тихо. Слишком тихо для этого места.")
	_update_help()


func _process(delta: float) -> void:
	if subtitle_timer > 0.0:
		subtitle_timer -= delta
		if subtitle_timer <= 0.0:
			subtitle.hide()


func say(line: String) -> void:
	subtitle_text.text = line
	subtitle.show()
	subtitle_timer = 5.0


func _unhandled_input(event: InputEvent) -> void:
	if not (event is InputEventKey and event.pressed and not event.echo):
		return
	# physical_keycode — чтобы клавиши работали и в русской раскладке.
	match event.physical_keycode:
		KEY_TAB:
			post.visible = not post.visible
		KEY_1:
			_add_param("color_levels", -1.0, 2.0, 64.0)
		KEY_2:
			_add_param("color_levels", 1.0, 2.0, 64.0)
		KEY_3:
			_add_param("dither_strength", -0.1, 0.0, 2.0)
		KEY_4:
			_add_param("dither_strength", 0.1, 0.0, 2.0)
		KEY_5:
			pixel_idx = (pixel_idx + 1) % PIXEL_PRESETS.size()
			mat.set_shader_parameter("pixel_res", PIXEL_PRESETS[pixel_idx])
		KEY_6:
			_add_param("tint_amount", -TINT_STEP, 0.0, 1.0)
		KEY_7:
			_add_param("tint_amount", TINT_STEP, 0.0, 1.0)
		KEY_8:
			_add_param("grain_amount", -0.01, 0.0, 0.2)
		KEY_9:
			_add_param("grain_amount", 0.01, 0.0, 0.2)
		KEY_0:
			tint_idx = (tint_idx + 1) % TINT_PRESETS.size()
			mat.set_shader_parameter("shadow_tint", TINT_PRESETS[tint_idx][1])
			mat.set_shader_parameter("highlight_tint", TINT_PRESETS[tint_idx][2])
		KEY_Q:
			_add_param("pixel_grid", -0.1, 0.0, 1.0)
		KEY_W:
			_add_param("pixel_grid", 0.1, 0.0, 1.0)
		KEY_A:
			_add_param("sharpen", -0.1, 0.0, 2.0)
		KEY_S:
			_add_param("sharpen", 0.1, 0.0, 2.0)
		KEY_D:
			dust.visible = not dust.visible
		KEY_H:
			help.visible = not help.visible
		_:
			return
	_update_help()


func _add_param(name: String, step: float, lo: float, hi: float) -> void:
	var v: float = mat.get_shader_parameter(name)
	mat.set_shader_parameter(name, clampf(v + step, lo, hi))


func _update_help() -> void:
	var res: Vector2 = mat.get_shader_parameter("pixel_res")
	help.text = "\n".join([
		"Tab  — эффект: %s" % ("ВКЛ" if post.visible else "выкл"),
		"1/2  — уровни цвета: %d" % int(mat.get_shader_parameter("color_levels")),
		"3/4  — дизеринг: %.1f" % mat.get_shader_parameter("dither_strength"),
		"5    — разрешение: %dx%d" % [res.x, res.y],
		"6/7  — сила тона: %.1f" % mat.get_shader_parameter("tint_amount"),
		"8/9  — зерно: %.2f" % mat.get_shader_parameter("grain_amount"),
		"0    — палитра: %s" % TINT_PRESETS[tint_idx][0],
		"Q/W  — сетка пикселей: %.1f" % mat.get_shader_parameter("pixel_grid"),
		"A/S  — резкость: %.1f" % mat.get_shader_parameter("sharpen"),
		"D    — пыль: %s" % ("ВКЛ" if dust.visible else "выкл"),
		"H    — скрыть подсказку",
	])
