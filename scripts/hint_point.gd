extends Marker2D
## Точка-подсказка в мире: на экране над ней рисуется значок (лупа или глаз),
## по клику внизу появляется текст. Значки создаёт street_ui.gd для всех точек
## из группы "hint_points". Точку можно класть внутрь слоя параллакса — значок
## поедет вместе с ним.

@export_enum("look", "eye") var icon: String = "look"
@export_multiline var text: String = ""


func _enter_tree() -> void:
	add_to_group("hint_points")
