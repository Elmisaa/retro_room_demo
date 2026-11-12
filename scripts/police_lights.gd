extends Node2D
## Мигалка служебной машины: красный и синий по очереди, с двойной вспышкой.
## Все дети, чьё имя начинается с "Red", включаются вместе с красной фазой,
## с "Blue" — с синей: свет (PointLight2D), свечение, заливка, блики на асфальте.
## Порядок нужных узлов свободный — можно добавлять новые.

@export var period := 0.7

var _t := 0.0
var _red: Array[CanvasItem] = []
var _blue: Array[CanvasItem] = []


func _ready() -> void:
	for c in get_children():
		if c is CanvasItem:
			if c.name.begins_with("Red"):
				_red.append(c)
			elif c.name.begins_with("Blue"):
				_blue.append(c)


func _process(delta: float) -> void:
	_t = fmod(_t + delta, period)
	var p := _t / period
	var red_on := p < 0.5 and fmod(p, 0.25) < 0.15
	var blue_on := p >= 0.5 and fmod(p - 0.5, 0.25) < 0.15
	for c in _red:
		c.visible = red_on
	for c in _blue:
		c.visible = blue_on
