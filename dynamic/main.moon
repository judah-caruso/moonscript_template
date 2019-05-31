require "src.GameController"

love.load = (arg) ->
    GameController.load({debug: true})

love.update = (dt) ->
    GameController.update(dt)

love.draw = ->
    GameController.draw!