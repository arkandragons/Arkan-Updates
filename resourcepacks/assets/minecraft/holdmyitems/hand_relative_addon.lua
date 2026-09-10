if P:isUsingItem(context.player) and I:isOf(context.item, Items:get("minecraft:potion")) then

	M:moveY(context.matrices, -0.05)

end

if P:isUsingItem(context.player) and I:isOf(context.item, Items:get("minecraft:honey_bottle")) then

	M:moveY(context.matrices, -0.05)

end

if P:isUsingItem(context.player) and I:isOf(context.item, Items:get("minecraft:ominous_bottle")) then

	M:moveY(context.matrices, -0.1)

end