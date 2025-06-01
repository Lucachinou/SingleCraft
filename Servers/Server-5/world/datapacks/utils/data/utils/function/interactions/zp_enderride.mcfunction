execute if block 5654 64 -5606 minecraft:lever[powered=false] run scoreboard players set EnderRide EnabledFeatures 0
execute if score EnderRide EnabledFeatures matches ..1 run data merge entity @e[tag=EnderRideValue,limit=1] {text:{"text":"Disabled","color":"red"}}
execute if block 5654 64 -5606 minecraft:lever[powered=true] run scoreboard players set EnderRide EnabledFeatures 1
execute if score EnderRide EnabledFeatures matches 1.. run data merge entity @e[tag=EnderRideValue,limit=1] {text:{"text":"Enabled","color":"green"}}