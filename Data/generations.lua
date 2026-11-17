local Generations = {}

Generations.TABLE = {
    [4]  = { generation = 4,  traitMax = 9, discMax = 9, bloodMax = 50, usableBlood = 50, perTurn = 10, doubleCost = false },
    [5]  = { generation = 5,  traitMax = 8, discMax = 8, bloodMax = 40, usableBlood = 40, perTurn = 8,  doubleCost = false },
    [6]  = { generation = 6,  traitMax = 7, discMax = 7, bloodMax = 30, usableBlood = 30, perTurn = 6,  doubleCost = false },
    [7]  = { generation = 7,  traitMax = 6, discMax = 6, bloodMax = 20, usableBlood = 20, perTurn = 4,  doubleCost = false },
    [8]  = { generation = 8,  traitMax = 5, discMax = 5, bloodMax = 15, usableBlood = 15, perTurn = 3,  doubleCost = false },
    [9]  = { generation = 9,  traitMax = 5, discMax = 5, bloodMax = 14, usableBlood = 14, perTurn = 2,  doubleCost = false },
    [10] = { generation = 10, traitMax = 5, discMax = 5, bloodMax = 13, usableBlood = 13, perTurn = 1,  doubleCost = false },
    [11] = { generation = 11, traitMax = 5, discMax = 5, bloodMax = 12, usableBlood = 12, perTurn = 1,  doubleCost = false },
    [12] = { generation = 12, traitMax = 5, discMax = 5, bloodMax = 11, usableBlood = 11, perTurn = 1,  doubleCost = false },
    [13] = { generation = 13, traitMax = 5, discMax = 5, bloodMax = 10, usableBlood = 10, perTurn = 1,  doubleCost = false },
    [14] = { generation = 14, traitMax = 5, discMax = 4, bloodMax = 10, usableBlood = 8,  perTurn = 1,  doubleCost = false },
    [15] = { generation = 15, traitMax = 5, discMax = 3, bloodMax = 10, usableBlood = 6,  perTurn = 1,  doubleCost = true  },
}

function Generations.get(genNumber)
    local g = math.floor(tonumber(genNumber) or 13)
    if g < 4 then g = 4 end
    if g > 15 then g = 15 end
    return Generations.TABLE[g]
end

return Generations
