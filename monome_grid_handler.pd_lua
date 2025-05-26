local monome_grid_handler = pd.Class:new():register("monome_grid_handler")

function monome_grid_handler:initialize(sel, atoms)
    -- Configure inlets and outlets
    self.inlets = 1  -- One inlet to receive the packed x, y, z values
    self.outlets = 0 -- No outlets as we'll use receivers instead

    -- Set up receiver name prefixes for each row
    self.transport_receiver = "transport"
    self.row_receiver_prefix = "row_"

    pd.post("monome_grid_handler: initialized")
    pd.post("monome_grid_handler: ready to handle grid key inputs")
    pd.post("monome_grid_handler: key (0,0) will send to '" .. self.transport_receiver .. "'")
    pd.post("monome_grid_handler: keys on rows 1-15 will send to '" .. self.row_receiver_prefix .. "N' where N is the row number (integer)")

    return true
end

-- Handle a list input from the monome grid
function monome_grid_handler:in_1_list(values)
    -- Check if we got the expected 3 values (x, y, z)
    if #values ~= 3 then
        self:error("monome_grid_handler: expected 3 values (x, y, z), got " .. #values)
        return
    end

    -- Explicitly convert coordinates to integers.
    -- math.floor ensures that if they come in as floats (e.g., 1.0),
    -- they are treated as integers for logic and string concatenation.
    local x = math.floor(values[1])  -- x coordinate (0-15, column)
    local y = math.floor(values[2])  -- y coordinate (0-15, row)
    local z = math.floor(values[3])  -- z value (1 = pressed, 0 = released)

    -- We only care about press events (z = 1), ignore release events (z = 0)
    if z ~= 1 then
        return
    end

    -- Handle transport button (0,0)
    if x == 0 and y == 0 then
      --  pd.post("monome_grid_handler: transport button pressed")
        -- Pd typically expects floats. Sending 1.0 for a 'bang' or toggle is common.
        pd.send(self.transport_receiver, "float", {1.0})
        return
    end

    -- Handle sample slicing rows (1-15)
    if y >= 1 and y <= 15 then
        -- Construct the receiver name using the integer y.
        -- Lua will convert the integer y to its string representation (e.g., "1", "2").
        local row_receiver = self.row_receiver_prefix .. y

        -- Send the column number (x) to the appropriate row receiver.
        -- The value sent will be treated as a float by Pd.
       -- pd.post(string.format("monome_grid_handler: key at row %d, column %d pressed - sending %d to %s",
          --  y, x, x, row_receiver))
        pd.send(row_receiver, "float", {tonumber(x)}) -- Ensure x is sent as a number
    end
end

-- Optional helper method to change receiver names if needed
function monome_grid_handler:in_1_set_transport_receiver(atoms)
    if #atoms > 0 and type(atoms[1]) == "string" then
        self.transport_receiver = atoms[1]
       -- pd.post("monome_grid_handler: transport receiver changed to '" .. self.transport_receiver .. "'")
    else
        self:error("monome_grid_handler: receiver name must be a symbol and be provided")
    end
end

function monome_grid_handler:in_1_set_row_prefix(atoms)
    if #atoms > 0 and type(atoms[1]) == "string" then
        self.row_receiver_prefix = atoms[1]
      --  pd.post("monome_grid_handler: row receiver prefix changed to '" .. self.row_receiver_prefix .. "'")
    else
        self:error("monome_grid_handler: prefix must be a symbol and be provided")
    end
end