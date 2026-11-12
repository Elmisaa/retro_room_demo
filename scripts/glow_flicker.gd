extends CanvasItem
## Мягкое свечение (аддитивный спрайт): лёгкое «дыхание» яркости
## и, по желанию, редкие короткие провалы — как у старой лампы или вывески.

@export var flicker := 0.06        ## Амплитуда плавного колебания (доля от базовой яркости)
@export var flicker_speed := 1.0   ## Скорость колебания
@export var blink_chance := 0.0    ## Сколько раз в секунду в среднем свет «моргает»
@export var blink_depth := 0.5     ## Насколько гаснет при моргании (0 — не гаснет, 1 — полностью)

var _base := 1.0
var _t := 0.0
var _blink := 0.0


func _ready() -> void:
	_base = modulate.a
	_t = randf() * 100.0


func _process(delta: float) -> void:
	_t += delta * flicker_speed
	var wave := (sin(_t * 2.3) + sin(_t * 5.1 + 1.7) * 0.5 + sin(_t * 0.7) * 0.6) / 2.1
	var a := _base * (1.0 + wave * flicker)
	if _blink > 0.0:
		_blink -= delta
		a *= 1.0 - blink_depth
	elif blink_chance > 0.0 and randf() < blink_chance * delta:
		_blink = randf_range(0.04, 0.14)
	modulate.a = a
