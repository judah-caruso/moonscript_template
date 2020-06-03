require "src.Configurator"


love.conf = (t) ->
    Configurator.load(t)
