-- Custom Items and Recipes Lua Mod

function get_mod_info()
    return {
        name = "Custom Items Mod",
        version = "1.0",
        author = "Jules AI"
    }
end

function on_survivor_action(survivor_name, action_id)
    -- Custom mod hook when survivor performs action
    return action_id
end
