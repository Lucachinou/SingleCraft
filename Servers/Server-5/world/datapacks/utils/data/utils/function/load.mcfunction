execute as @e[type=armor_stand,tag=SpawnUtilsData] run kill @s
execute as @e[type=armor_stand,tag=SpawnUtilsDataMushroom] run kill @s
summon armor_stand 5664 63 -5606 {Invisible:1b,NoGravity:1b,Tags:["SpawnUtilsData"]}
summon armor_stand -1818 63 -15205 {Invisible:1b,NoGravity:1b,Tags:["SpawnUtilsDataMushroom"]}
tellraw @a {"text":"Datapack loaded!","color":"gray", bold:true}