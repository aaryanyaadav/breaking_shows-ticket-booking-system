-- Lua script for atomic multi-seat hold reservation in Redis
-- KEYS: List of seat hold keys (e.g. hold:{show_id}:{seat_id})
-- ARGV[1]: hold_token
-- ARGV[2]: user_id
-- ARGV[3]: ttl_seconds

local hold_token = ARGV[1]
local user_id = ARGV[2]
local ttl_seconds = tonumber(ARGV[3])
local payload = hold_token .. ":" .. user_id

-- Phase 1: Check if ANY requested seat is already held
for i, key in ipairs(KEYS) do
    if redis.call("EXISTS", key) == 1 then
        -- Seat is occupied/held by another user or session
        return {0, key}
    end
end

-- Phase 2: Acquire ALL seat holds atomically
for i, key in ipairs(KEYS) do
    redis.call("SET", key, payload, "EX", ttl_seconds)
end

return {1, "OK"}
