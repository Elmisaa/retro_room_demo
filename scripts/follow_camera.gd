extends Node2D
## Держит узел над камерой (со смещением). Нужен излучателям дождя:
## они всегда сыплют капли над видимой частью улицы, а сами капли
## (local_coords = false) летят в мире и не «едут» вместе с камерой.

@export var offset := Vector2.ZERO


func _process(_delta: float) -> void:
	var cam := get_viewport().get_camera_2d()
	if cam:
		var cx: float = cam.get_meta("true_x", cam.global_position.x)
		global_position = Vector2(cx, cam.global_position.y) + offset
