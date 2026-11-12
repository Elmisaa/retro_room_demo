extends Node
## Окно с «больной» проводкой: обычно горит; раз в несколько секунд свет
## начинает мигать и иногда гаснет на время, потом с миганием включается снова.
##  - off_mask — тёмная маска поверх светлого стекла (видна = окно погасло);
##  - glow — свечение этого окна (выключается вместе с окном).

@export var off_mask: CanvasItem
@export var glow: CanvasItem
@export var min_wait := 10.0
@export var max_wait := 25.0
@export var off_chance := 0.6       ## вероятность, что после мигания окно погаснет
@export var min_off := 4.0
@export var max_off := 10.0
@export var first_wait := 6.0

enum { ON, FLICKER, OFF }
var _state := ON
var _timer := 0.0
var _flick := 0.0
var _go_off := false


func _ready() -> void:
	_timer = first_wait
	_set_lit(true)


func _process(delta: float) -> void:
	_timer -= delta
	match _state:
		ON:
			if _timer <= 0.0:
				_start_flicker(randf() < off_chance)
		OFF:
			if _timer <= 0.0:
				_start_flicker(false)
		FLICKER:
			_flick -= delta
			if _flick <= 0.0:
				_flick = randf_range(0.03, 0.12)
				_set_lit(not _is_lit())
			if _timer <= 0.0:
				if _go_off:
					_state = OFF
					_timer = randf_range(min_off, max_off)
					_set_lit(false)
				else:
					_state = ON
					_timer = randf_range(min_wait, max_wait)
					_set_lit(true)


func _start_flicker(go_off: bool) -> void:
	_state = FLICKER
	_go_off = go_off
	_timer = randf_range(0.5, 1.3)
	_flick = 0.0


func _is_lit() -> bool:
	return off_mask == null or not off_mask.visible


func _set_lit(lit: bool) -> void:
	if off_mask:
		off_mask.visible = not lit
	if glow:
		glow.visible = lit
