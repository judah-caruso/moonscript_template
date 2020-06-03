module "Logger", package.seeall
export log

lume = require("lume")

log = (t = "", id, msg) ->

    _msg = msg

    if string.match(string.sub(msg, -1), "%p")
        return error(lume.format("Logger message: '{1}' ends in punctuation!", {msg}))

    switch t\lower()
        when "warning"
            return print(lume.format("[{id}] Warning: {msg}.", {id:id\upper(), msg:_msg}))
        when "error"
            return error(lume.format("[{id}] Error: {msg}.", {id:id\upper(), msg:_msg}))
        else
            return print(lume.format("[{id}] {msg}.", {id:id\upper(), msg:_msg}))
