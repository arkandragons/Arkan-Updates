local l = (context.bl and 1) or -1
local player = context.player
local item = context.item
local matrices = context.matrices
local mainHand = context.mainHand

local potion = {
	"minecraft:potion",
	"minecraft:dragon_breath",
	"minecraft:glass_bottle",
	"minecraft:splash_potion",
	"minecraft:lingering_potion",
	"minecraft:experience_bottle",
	"farmersdelight:milk_bottle"
	
}

for i, id in pairs(potion) do
	if I:isOf(item, Items:get(id)) and not P:isUsingItem(player) then
	M:scale(matrices, 0.95, 0.95, 0.95)
	M:rotateX(matrices, -150)
	M:rotateY(matrices, 20 * l)
	M:moveY(matrices, -0.35)
	M:rotateZ(matrices, 170 * l)
	M:moveZ(matrices, 0.1)
	return
	end
end

if I:isOf(item, Items:get("minecraft:ominous_bottle")) and not P:isUsingItem(player) then
    M:scale(matrices, 0.95, 0.95, 0.95)
	M:rotateX(matrices, -150)
	M:rotateY(matrices, 20 * l)
	M:moveY(matrices, -0.40)
	M:rotateZ(matrices, 170 * l)
	M:moveZ(matrices, 0.1)
	return
end


if I:isOf(item, Items:get("minecraft:honey_bottle")) and not P:isUsingItem(player) then
	M:scale(matrices, 0.95, 0.95, 0.95)
	M:rotateX(matrices, -175)
	M:rotateY(matrices, 20 * l)
	M:rotateZ(matrices, 185 * l)
	M:moveY(matrices, 0.20)
	M:moveX(matrices, 0.05 * l)
	M:moveZ(matrices, -0.05)
end

if P:isUsingItem(player) and I:isOf(item, Items:get("minecraft:honey_bottle")) then
	M:scale(matrices, 1.0, 1.0, 1.0)
	M:rotateX(matrices, -50)
	M:rotateY(matrices, 05 * l)
	M:rotateZ(matrices, 20 * l)
	M:moveY(matrices, 0.05)
	M:moveX(matrices, 0.05 * l)
	M:moveZ(matrices, 0.22)
end

if P:isUsingItem(player) and I:isOf(item, Items:get("minecraft:ominous_bottle")) then
	M:scale(matrices, 1.0, 1.0, 1.0)
	M:rotateX(matrices, -50)
	M:rotateY(matrices, 05 * l)
	M:rotateZ(matrices, 20 * l)
	M:moveY(matrices, 0.05)
	M:moveX(matrices, 0.05 * l)
	M:moveZ(matrices, 0.2)
end

if P:isUsingItem(player) and I:isOf(item, Items:get("minecraft:potion")) then
	M:scale(matrices, 1.0, 1.0, 1.0)
	M:rotateX(matrices, -50)
	M:rotateY(matrices, 05 * l)
	M:rotateZ(matrices, 20 * l)
	M:moveY(matrices, 0.05)
	M:moveX(matrices, 0.05 * l)
	M:moveZ(matrices, 0.2)
end



if P:isUsingItem(player) and I:isOf(item, Items:get("farmersdelight:milk_bottle")) then
	M:scale(matrices, 1.0, 1.0, 1.0)
	M:rotateX(matrices, -50)
	M:rotateY(matrices, 05 * l)
	M:rotateZ(matrices, 20 * l)
	M:moveY(matrices, 0.05)
	M:moveX(matrices, 0.05 * l)
	M:moveZ(matrices, 0.2)
end
