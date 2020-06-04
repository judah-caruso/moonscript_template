require "src.Runner"

love.load = (arg) ->
    Runner.load({debug: true})

love.update = (dt) ->
    Runner.update(dt)

love.draw = ->
    Runner.draw!
