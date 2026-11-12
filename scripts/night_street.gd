extends Node2D
## Сцена «Улица»: ночная улица из пакета references/US_1997_Night_Street_Godot,
## слои параллакса, полицейский, свет. Управление: A/D или стрелки — идти, Esc — меню.
##
## Начало сцены: патрульный выходит из служебной машины — «поднимается» из-за неё
## (вышел с пассажирской стороны на тротуар), проявляется и сам отходит на пару шагов,
## после чего управление переходит игроку.
##
## Плавная пиксельная камера:
##  - точная позиция камеры C = герой + упреждение (упреждение кратно 3 px);
##  - Camera2D стоит в S = floor(C / 3) * 3 — мир всегда лежит на сетке шейдера;
##  - остаток (C - S) / 3 уходит в шейдер (scroll_frac) и сдвигает готовую картинку.
## Герой округляется тем же floor, поэтому на экране стоит неподвижно, а улица
## едет плавно. Слои параллакса берут точную C из meta "true_x".
##
## Слои выставлены так, что в правом конце улицы кадр совпадает с исходным
## референсом (anchor_x = RIGHT_CAM_X у слоёв с параллаксом).

const PIXEL := 3.0
const HALF_W := 480.0
const WORLD_W := 2172.0
const RIGHT_CAM_X := WORLD_W - HALF_W
const LOOKAHEAD := 90.0
## Сценка выхода из машины.
const EXIT_X := 1845.0        ## у двери служебной машины
const EXIT_WALK_TO := 1590.0  ## куда он сам отходит (перед капотом)
const EXIT_WAIT := 0.6        ## пауза перед выходом
const EXIT_RISE := 0.45       ## сколько длится «подъём» из-за машины
const EXIT_DROP := 45.0       ## насколько ниже начинается подъём, px

@onready var cam: Camera2D = $Camera
@onready var player: Node2D = $World/Player
@onready var post_mat: ShaderMaterial = $PostFX/Effect.material

var _look := LOOKAHEAD
var _intro_t := 0.0
var _intro := true
@onready var _sprite: Sprite2D = $World/Player/Sprite
@onready var _shadows: Node2D = $World/Player/Shadows


func _ready() -> void:
	# Герой считает свою позицию раньше камеры — иначе он дрожал бы на кадр.
	player.process_priority = -10
	_start_intro()
	_update_camera()


func _start_intro() -> void:
	player.set("_x", EXIT_X)
	player.position.x = EXIT_X
	player.set("facing", -1.0)
	player.set("input_enabled", false)
	_sprite.flip_h = true
	_sprite.modulate.a = 0.0
	_sprite.position.y = EXIT_DROP
	_shadows.visible = false
	_look = -LOOKAHEAD


func _update_intro(delta: float) -> void:
	_intro_t += delta
	var k := clampf((_intro_t - EXIT_WAIT) / EXIT_RISE, 0.0, 1.0)
	k = 1.0 - (1.0 - k) * (1.0 - k)  # плавный подъём
	_sprite.modulate.a = clampf(k * 1.6, 0.0, 1.0)
	_sprite.position.y = roundf(EXIT_DROP * (1.0 - k))
	if k >= 1.0:
		_shadows.visible = true
		if float(player.get("_x")) > EXIT_WALK_TO:
			player.set("auto_dir", -1.0)
		else:
			player.set("auto_dir", 0.0)
			player.set("input_enabled", true)
			_intro = false


func _process(delta: float) -> void:
	if _intro:
		_update_intro(delta)
	var facing: float = player.get("facing")
	_look = lerpf(_look, facing * LOOKAHEAD, 1.0 - exp(-delta * 2.0))
	_update_camera()


func _update_camera() -> void:
	var look := snappedf(_look, PIXEL)
	# Точная позиция округляется до целого пикселя окна: так сдвиг в шейдере
	# всегда целый, и «большие» пиксели не меняют ширину (2–4 px) при прокрутке.
	var c := roundf(clampf(float(player.get("_x")) + look, HALF_W, RIGHT_CAM_X))
	var s := floorf(c / PIXEL) * PIXEL
	cam.position = Vector2(s, 362.0)
	cam.set_meta("true_x", c)
	post_mat.set_shader_parameter("scroll_frac", Vector2((c - s) / PIXEL, 0.0))
	# Узор дизеринга едет вместе с миром — иначе при ходьбе картинка «кипит».
	post_mat.set_shader_parameter("dither_offset", Vector2((s - HALF_W) / PIXEL, 0.0))
