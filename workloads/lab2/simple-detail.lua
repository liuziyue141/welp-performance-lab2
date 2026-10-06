local socket = require("socket")
math.randomseed(socket.gettime()*1000)
math.random(); math.random(); math.random()

char_to_hex = function(c)
    return string.format("%%%02X", string.byte(c))
end
  
function urlencode(url)
    if url == nil then
        return
    end
    url = url:gsub("\n", "\r\n")
    url = url:gsub("([^%w ])", char_to_hex)
    url = url:gsub(" ", "+")
    return url
end
  
hex_to_char = function(x)
    return string.char(tonumber(x, 16))
end
  
urldecode = function(url)
    if url == nil then
        return
    end
    url = url:gsub("+", " ")
    url = url:gsub("%%(%x%x)", hex_to_char)
    return url
end


-- Load the data from the CSV file into a table
local samples = {}
local file = io.open("./samples/detail_samples.csv", "r")

-- Skip the first line containing headers
file:read("*line")

for line in file:lines() do
    local restaurant_name, location, style, capacity = line:match("\"(.-)\",\"(.-)\",\"(.-)\",(%d+)")
    -- print(restaurant_name, location, style, capacity) -- (optional) toggle to look at data
    if restaurant_name and location and style and capacity then
        table.insert(samples, {restaurant_name = restaurant_name, location = location, style = style, capacity = tonumber(capacity)})
    end
end
file:close()

local function post_detail()
    local method = "GET"

    -- Choose a random sample to post from the loaded detail data
    local random_index = math.random(1, #samples)
    local sample = samples[random_index]

    -- Construct the path using the selected sample
    local path = url .. "/post-detail?restaurant_name=" .. urlencode(sample.restaurant_name) .. "&location=" .. urlencode(sample.location) .. "&style=" .. urlencode(sample.style) .. "&capacity=" .. sample.capacity
    -- print(path) -- (optional) uncomment me to print the URL query!
    local headers = {}
    return wrk.format(method, path, headers, nil)
end

local function get_detail()
    local method = "GET"

    -- Choose a random sample to get from the loaded detail data
    local random_index = math.random(1, #samples)
    local sample = samples[random_index]

    -- Construct the path using the selected sample
    local path = url .. "/get-detail?restaurant_name=" .. urlencode(sample.restaurant_name)
    -- print(path) -- (optional) uncomment me to print the URL query!
    local headers = {}
    return wrk.format(method, path, headers, nil)
end

request = function()
    cur_time = math.floor(socket.gettime())
    local post_detail_ratio  = 0.2
    local get_detail_ratio   = 1 - post_detail_ratio
  
    local coin = math.random()
    if coin < post_detail_ratio then
      return post_detail(url)
    else
      return get_detail(url)
    end
end
