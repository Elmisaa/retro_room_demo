extends Node2D
## Полицейский: ходьба влево/вправо (A/D или стрелки), анимация по кадрам.
## Кадры спрайт-листа: [покой × idle_count][шаг × walk_count].

@export var speed := 165.0
@export var min_x := 40.0
@export var max_x := 3560.0
@export var idle_count := 2
@export var idle_fps := 1.2
@export var walk_count := 6
@export var walk_fps := 9.0
## Округление позиции до сетки пикселей шейдера: "round" или "floor"
## (плавная камера улицы считает от floor, чтобы герой не дрожал на экране).
@export var snap_floor := false

@onready var sprite: Sprite2D = $Sprite

var input_enabled := true
## Автоходьба для сценок (-1 влево, 1 вправо, 0 — нет): работает и без ввода.
var auto_dir := 0.0
var walking := false
var facing := 1.0
var _x := 0.0
var _anim_t := 0.0


func _ready() -> void:
	_x = position.x


func _process(delta: float) -> void:
	var dir := auto_dir
	if input_enabled and auto_dir == 0.0:
		if Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT):
			dir -= 1.0
		if Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT):
			dir += 1.0

	if (dir != 0.0) != walking:
		_anim_t = 0.0
	walking = dir != 0.0
	if walking:
		facing = dir
		sprite.flip_h = dir < 0.0
		_x = clampf(_x + dir * speed * delta, min_x, max_x)
	# Привязка к сетке «больших» пикселей, чтобы персонаж не дрожал под шейдером.
	position.x = floorf(_x / 3.0) * 3.0 if snap_floor else snappedf(_x, 3.0)

	_anim_t += delta
	if walking:
		sprite.frame = idle_count + int(_anim_t * walk_fps) % walk_count
	else:
		sprite.frame = int(_anim_t * idle_fps) % idle_count
