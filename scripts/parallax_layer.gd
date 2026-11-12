extends Node2D
## Слой параллакса: движется медленнее камеры (factor < 1, дальние планы)
## или быстрее (factor > 1, передний план).
## Позиция округляется до 3 px — размера «большого» пикселя шейдера
## (320×240 при окне 960×720), чтобы слои не дрожали на пиксельной сетке.

@export var factor := 1.0
## x камеры, при котором слой стоит на своём месте (как в исходной композиции).
@export var anchor_x := 480.0
## Округлять позицию до 3 px. Для плавной камеры (night_street.gd) выключается:
## слой едет плавно, а сетку пикселей держит шейдер.
@export var snap := true

const PIXEL := 3.0


func _process(_delta: float) -> void:
	var cam := get_viewport().get_camera_2d()
	if cam == null:
		return
	# Плавная камера кладёт свою точную (не округлённую) позицию в meta "true_x".
	var cx: float = cam.get_meta("true_x", cam.global_position.x)
	var x := (cx - anchor_x) * (1.0 - factor)
	position.x = snappedf(x, PIXEL) if snap else roundf(x)
