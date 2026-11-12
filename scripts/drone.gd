extends Node2D
## Полицейский дрон: держится над патрульным, неторопливо смещаясь
## из стороны в сторону, и водит прожектором. Пятно света (PointLight2D)
## ставится туда, где луч падает на тротуар.

@export var sway := 330.0         ## Насколько дрон уходит от центра кадра
@export var sway_speed := 0.12    ## Как быстро он смещается (циклов в секунду)
@export var follow := 0.6         ## Насколько плотно он догоняет камеру
@export var ground_y := 470.0

@onready var beam: Sprite2D = $Beam
@onready var spot: PointLight2D = $Spot

var _t := 0.0
var _x := 0.0
var _base_y := 0.0


func _ready() -> void:
	_base_y = position.y
	_x = position.x


func _process(delta: float) -> void:
	_t += delta
	var cam := get_viewport().get_camera_2d()
	var center := cam.global_position.x if cam else _x
	var target := center + sin(_t * sway_speed * TAU) * sway
	_x = lerpf(_x, target, 1.0 - exp(-delta * follow))
	var y := _base_y + sin(_t * 1.7) * 4.0
	position = Vector2(snappedf(_x, 3.0), snappedf(y, 3.0))

	var angle := sin(_t * 0.55) * 0.38
	beam.rotation = angle
	var dy := ground_y - position.y
	spot.position = Vector2(-tan(angle) * dy, dy)
