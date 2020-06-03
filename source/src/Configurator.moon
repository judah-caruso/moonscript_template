module "Configurator", package.seeall
export load, reload, set_value, get_value, remove

inspect = require("inspect")
lume    = require("lume")

-- a table that's used to configure the love engine.
conf = {
    _lambda_engine: { -- a table that gets written directly into love's config
        file_name: "lambda_config"
        engine_version: "0.0.1",
        build_title: "Untitled",
        build_version: "0.0.1",
        build_flavor: "",
        build_number: "0",
        config_edit_number: 0,
        config_refresh_number: 0,
    },
    debug: {
        enable_console: true,
    },
    backend: {
        has_loaded_config: false,
        engine_version: "11.0",
        save_dir: nil,
        check_save_dir_first: false,
        mobile_accelerometer_joystick: false,
        mobile_save_to_external: false,
        mobile_mix_with_audiosystem: true,
        modules: {
            enable_audio: true,
            enable_sound: true,
            enable_data: true,
            enable_event: true,
            enable_font: true,
            enable_graphics: true,
            enable_image: true,
            enable_joystick: true,
            enable_keyboard: true,
            enable_math: true,
            enable_mouse: true,
            enable_physics: true,
            enable_system: true,
            enable_thread: true,
            enable_timer: true,
            enable_touch: true,
            enable_video: true,
            enable_window: true,
        }
    },
    client: {
        title: "Game",
        window: {
            monitor: 1,
            icon: nil,
            borderless: false,
            resizable: false,
            fullscreen: false,
            fullscreen_type: "desktop", -- (desktop, exclusive)
            high_dpi: false,
            x: nil,
            y: nil,
            min_width: 800,
            min_height: 600
            max_width: 800,
            max_height: 600,
        },
        graphics: {
            vsync: 1,
            msaa: 0,
            depth: nil,
            stencil: nil,
            gamma_correct: false,
        }
    }
}


-- Returns a table of the previously used engine configuration file
read_config_as_table = () ->
    file = io.open(conf._lambda_engine.file_name)
    if file == nil
        return Logger.log("error", "read_config_as_table", "Unable to open engine configuration file")

    file_string = file\read("*a")
    file\close()

    old_config = lume.deserialize(file_string)
    return old_config


-- Returns a write filehandler for the engine configuration file
open_config_writer = () ->
    file = io.open(conf._lambda_engine.file_name, "w+")
    if file == nil
        return Logger.log("error", "open_config_writer", "Unable to create engine configuration file")

    return file


-- _deep_search(table, {"nested_table_1", "nested_table_2"})
_deep_search = (t, s) ->
    ret = nil

    if #s <= 1 and t[s[1]] != nil
        return t[s[1]]

    for key, value in pairs(t)
        for _, search in pairs(s)
            if key == search
                if type(value) != "table"
                    ret = t
                    break

                return _deep_search(value, {unpack(s, 2, #s)})

    if ret == nil
        return Logger.log("error", "get_value", "'" .. inspect(s) .. "' was not found in configuration file")

    return ret


-- _deep_replace(table, {"nested_table_1", "nested_table_2", "nested_value"}, "replacement_value")
_deep_replace = (t, s, v) ->
    ret = nil

    for key, value in pairs(t)
        for _, search in pairs(s)
            if key == search
                if type(value) != "table"
                    t[key] = v
                    ret = key
                    break

                return _deep_replace(value, {unpack(s, 2, #s)}, v)

    if ret == nil
        return Logger.log("error", "set_value", "'" .. inspect(s) .. "' was not found in configuration file")

    return ret


-- Takes a string in the format of "key.key.key" and sets the last's value to v
set_value = (ar, f, v) ->
    keys = [key for key in f\gmatch("[^.]+")]

    if conf[keys[1]] == nil
        return Logger.log("error", "set_value", "Field '".. keys[1] .."' does not exist in configuration file")

    _deep_replace(conf, keys, v)
    conf._lambda_engine.config_edit_number += 1

    -- todo: atomic bool should change dynamically depending on what we changed
    reload(ar)


-- Takes a string in the format of "key.key.key" and returns the last value
-- "*" to return the entire config
get_value = (f) ->
    if f == "*" return conf

    keys = [key for key in f\gmatch("[^.]+")]

    if conf[keys[1]] == nil
        return Logger.log("error", "get_value", "Field '".. keys[1] .."' does not exist in configuration file")

    val = _deep_search(conf, keys)

    return val


reload = (atomic_reload = false) ->
    old_config = read_config_as_table()
    conf._lambda_engine.config_refresh_number += 1

    if atomic_reload
        love.init()
    else
        love.conf(old_config)


-- Overwrites the old engine config with the new one
write = (t) ->
    file = open_config_writer()
    file\write(lume.serialize(t))
    file\close()


remove = () ->
    ok, err = os.remove(conf._lambda_engine.file_name)
    if err != nil
        Logger.log("error", "remove", err)

    return ok


load = (t) ->
    -- =======
    -- MODULES (what the engine should load)
    -- =======
        -- Audio/Visual
    t.modules.audio     = conf.backend.modules.enable_audio
    t.modules.sound     = conf.backend.modules.enable_sound
    t.modules.video     = conf.backend.modules.enable_video
    t.modules.graphics  = conf.backend.modules.enable_graphics
    t.modules.image     = conf.backend.modules.enable_image
    t.modules.font      = conf.backend.modules.enable_font
        -- Systems
    t.modules.system    = conf.backend.modules.enable_system
    t.modules.event     = conf.backend.modules.enable_event
    t.modules.data      = conf.backend.modules.enable_data
    t.modules.thread    = conf.backend.modules.enable_thread
    t.modules.physics   = conf.backend.modules.enable_physics
    t.modules.math      = conf.backend.modules.enable_math
    t.modules.window    = conf.backend.modules.enable_window
    t.modules.timer     = conf.backend.modules.enable_timer
        -- Input
    t.modules.mouse     = conf.backend.modules.enable_mouse
    t.modules.keyboard  = conf.backend.modules.enable_keyboard
    t.modules.joystick  = conf.backend.modules.enable_joystick
    t.modules.touch     = conf.backend.modules.enable_touch

    -- =====
    -- DEBUG
    -- =====
    t.console  = conf.debug.enable_console

    -- =======
    -- BACKEND (non-client-modifiable configuration values)
    -- =======
    t.identity              = conf.backend.save_dir
    t.appendidentity        = conf.backend.check_save_dir_first
    t.version               = conf.backend.engine_version
    t.accelerometerjoystick = conf.backend.mobile_accelerometer_joystick
    t.externalstorage       = conf.backend.mobile_save_to_external
    t.audio.mixwithsystem   = conf.backend.mobile_mix_with_audiosystem

    -- ========
    -- FRONTEND
    -- ========
        -- Non-configurable
    t.title                 = conf.client.title
    t.window.title          = conf.client.title
    t.window.icon           = conf.client.window.icon
    t.window.x              = conf.client.window.x
    t.window.y              = conf.client.window.y

        -- Configurable
    t.window.vsync          = conf.client.graphics.vsync
    t.window.msaa           = conf.client.graphics.msaa
    t.window.depth          = conf.client.graphics.depth   -- non-configurable?
    t.window.stencil        = conf.client.graphics.stencil -- non-configurable?
    t.window.borderless     = conf.client.window.borderless
    t.window.display        = conf.client.window.monitor
    t.window.fullscreen     = conf.client.window.fullscreen
    t.window.fullscreentype = conf.client.window.fullscreen_type
    t.window.width          = conf.client.window.max_width
    t.window.height         = conf.client.window.max_height
    t.window.minwidth       = conf.client.window.min_width
    t.window.minheight      = conf.client.window.min_height
    t.window.resizable      = conf.client.window.resizable  -- non-configurable?
    t.window.highdpi        = conf.client.window.high_dpi
    t.gammacorrect          = conf.client.graphics.gamma_correct -- non-configurable?

    t._lambda_engine        = conf._lambda_engine

    -- save our config to a file we can use in our reload function
    write(t)

    conf.backend.has_loaded_config = true
