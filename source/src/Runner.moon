module "Runner", package.seeall
export load, update, draw

require "src.Configurator"
require "src.Logger"
inspect = require("inspect")

status  = ""
version = ""
preload_finished = false

preload = (debug = false) ->
    Logger.log(nil, "preload", "Starting preload")

    if debug
        Logger.log(nil, "preload", "Debug flag set on")

    -- load standard assets

    preload_finished = true
    Logger.log(nil, "preload", "Finished")


load = (debug = false) ->
    if not preload_finished
        preload(debug)

    if debug
        Logger.log(nil, "load", "Debug flag set on")

    -- load/initialize non-assets

    status = "Initial load finished!"
    Logger.log(nil, "load", "Finished")


update = (dt) ->
    love.keypressed = (key, scancode, isrepeat) ->
        if key == "r"
            -- reloads the current configuration
            status = Configurator.get_value("_lambda_engine")
            Configurator.reload(true)
        if key == "q"
            Configurator.remove()
            love.event.quit()


draw = () ->
    love.graphics.print("Status: " .. inspect(status), 0, 0)
