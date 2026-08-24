-- Lua script for releasing seat holds safely in Redis
-- KEYS: List of seat hold keys
-- ARGV[1]: hold_token

local hold_token = ARGV[1]
local released_count = 0

for i, key in ipairs(KEYS) do
    local val = redis.call("GET", key)
    if val then
        -- Check if the token matches
        local token_in_redis = string.match(val, "([^:]+)")
        if token_in_redis == hold_token then
            redis.call("DEL", key)
            released_count = released_count + 1
        end
    end
end

return released_count
