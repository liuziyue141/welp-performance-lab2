local function post_detail()
    local method = "GET"
    path = url .. "/post-detail?restaurant_name=Microsoft+Cafe&location=3785+Jefferson+Rd+NE&style=Stale+Food&capacity=100"
    local headers = {}
    return wrk.format(method, path, headers, nil)
end

request = function()
    return post_detail(url)
end