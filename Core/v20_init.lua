V20 = V20 or {
    Traits             = require("Data.attributes_abilities"),
    Generations        = require("Data.generations"),
    Clans              = require("Data.clans"),
    MoralityCatalog    = require("Data.morality_virtues"),
    DisciplinesCatalog = require("Data.disciplines_catalog"),
    BackgroundsCatalog = require("Data.backgrounds_catalog"),
    MeritsFlawsCatalog = require("Data.merits_flaws_catalog"),

    Dice               = require("Core.dice"),
    Blood              = require("Core.generation_blood"),
    Health             = require("Core.health"),
    WillpowerMorality  = require("Core.willpower_morality"),
    DisciplinesEngine  = require("Core.disciplines_engine"),
    BackgroundsEngine  = require("Core.backgrounds_engine"),
    Creation           = require("Core.creation"),
    Experience         = require("Core.experience"),
    ClanWeaknesses     = require("Core.clan_weaknesses"),
}

V20.ClanWeaknesses = V20.ClanWeaknesses or require("Core.clan_weaknesses")

return V20
