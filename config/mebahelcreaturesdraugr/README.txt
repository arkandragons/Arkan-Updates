Mebahel's Draugr Creatures - Configuration Guide
================================================

All configuration files are located in this folder and are regenerated with valid values when required.
Health values use health points (2 health points = 1 heart). Percentages use values from 0 to 100.

1) entity_health_config.json
-----------------------------
Sets maximum health. Valid range: 0 to 100000.
  draugrEntityHealth: basic Draugr (default 30)
  draugrArcherEntityHealth: Draugr Archer (default 30)
  draugrWightEntityHealth: Draugr Wight (default 34)
  draugrScourgeEntityHealth: Draugr Scourge (default 38)
  draugrOverlordEntityHealth: Draugr Overlord (default 400)
  skeletonWarriorEntityHealth: Skeleton Warrior (default 26)
  skeletonWarriorHeadEntityHealth: Skeleton Warrior Head (default 8)
  flameAtronachEntityHealth: Flame Atronach (default 32)
  infernalDraugrEntityHealth: Infernal Draugr (default 42)

2) entity_armor_config.json
----------------------------
Sets armor points. Valid range: 0 to 1024.
  draugrEntityArmor: basic Draugr (default 5)
  draugrArcherEntityArmor: Draugr Archer (default 3)
  draugrWightEntityArmor: Draugr Wight (default 5)
  draugrScourgeEntityArmor: Draugr Scourge (default 3)
  draugrOverlordEntityArmor: Draugr Overlord (default 15)
  skeletonWarriorEntityArmor: Skeleton Warrior (default 4)
  skeletonWarriorHeadEntityArmor: Skeleton Warrior Head (default 2)
  flameAtronachEntityArmor: Flame Atronach (default 4)
  infernalDraugrEntityArmor: Infernal Draugr (default 6)

3) entity_damage_config.json
-----------------------------
Sets attack damage. Valid range: 0 to 100.
  draugrEntityMeleeDamage: basic Draugr melee damage (default 6)
  draugrArcherEntityBonusArrowDamage: bonus added to arrow damage (default 0)
  draugrWightEntityMeleeDamage: Wight melee damage (default 6)
  draugrWightEntityFrostbiteDamage: Wight frostbite damage (default 2.5)
  draugrScourgeEntityFrostbiteDamage: Scourge frostbite damage (default 3)
  draugrScourgeEntityIceSpikeDamage: Scourge ice spike damage (default 9)
  draugrOverlordEntityMeleeDamage: Overlord melee damage (default 12)
  draugrOverlordEntitySpinDamage: Overlord spin damage (default 10)
  draugrOverlordEntityGroundStrikeDamage: Overlord ground-strike damage (default 20)
  skeletonWarriorEntityMeleeDamage: Skeleton Warrior melee damage (default 5)
  flameAtronachEntityDamage: Flame Atronach attack damage (default 8)
  infernalDraugrEntityMeleeDamage: Infernal Draugr melee damage (default 7)
  infernalDraugrEntityFireBoltDamage: Infernal Draugr firebolt damage (default 8)

4) combat_balancing_config.json
--------------------------------
  draugrMinBlockProbability: minimum Draugr/Wight block chance (default 8%)
  draugrMaxBlockProbability: maximum Draugr/Wight block chance at low health (default 16%)
  draugrOverlordMinBlockProbability: minimum Overlord block chance (default 10%)
  draugrOverlordMaxBlockProbability: maximum Overlord block chance at low health (default 20%)
  draugrSpawnWithPotionProbability: chance to spawn with a potion (default 5%, valid above 0 through 100)
  draugrRaidScalingDifficulty: enables raid difficulty scaling (default true)
  flameAtronachSummonDurationInSecond: summoned Atronach lifetime in seconds (default 120)
  infernalDraugrMeleeDodgeProbability: chance to dodge melee attacks (default 10%, valid above 0 through 100)

5) spawn_rate_config.json
-------------------------
Spawn weights range from 0 to 10. Higher values increase spawn frequency; 0 disables natural spawning.
All fields default to 10: draugrSpawnRate, draugrArcherSpawnRate, draugrWightSpawnRate,
draugrScourgeSpawnRate, skeletonWarriorSpawnRate, flameAtronachSpawnRate, and infernalDraugrSpawnRate.

6) multiplayer_chest_config.json
---------------------------------
  turnOnMultiplayerDraugrChest: enables multiplayer Draugr chest behavior (default true)

7) spell_caster_trap_config.json
---------------------------------
Contains playerTraps and dungeonTraps groups. Each group has firebolt, frostbite, and frostSpike entries.
  damage: projectile damage (valid 0 to 100)
  range: target acquisition range in blocks (valid 1 to 128)
  cooldownTicks: delay between attacks (20 ticks = 1 second; valid 1 to 72000)
  soulsPerShot: souls consumed per projectile; present only under playerTraps and must be 0 or greater
Player defaults: firebolt 7 damage, 24 range, 120 ticks, 4 souls; frostbite 3 damage, 18 range, 150 ticks, 1 soul; frostSpike 8 damage, 24 range, 120 ticks, 5 souls.
Dungeon defaults: firebolt 7 damage, 24 range, 80 ticks; frostbite 3 damage, 18 range, 100 ticks; frostSpike 8 damage, 24 range, 80 ticks. Dungeon traps consume no souls.

8) draugr_raid_config.json
----------------------------
Customizes the number and content of Draugr Raid waves.
  normalDifficultyWaves: waves used before the Nether difficulty upgrade.
  netherDifficultyWaves: waves used after the Nether difficulty upgrade.
Each entry in a list represents one wave. Adding or removing entries changes the number of waves. At least one wave is required.
  mobCount: total number of regular enemies spawned in the wave (0 to 500).
  draugrWeight, skeletonWarriorWeight, draugrArcherWeight, draugrWightWeight, draugrScourgeWeight: relative chances of selecting each enemy.
A weight of 0 disables that enemy for the wave. Larger weights make it more common compared with the other enabled enemies.
  overlordCount: number of Draugr Overlords added to the wave (0 to 500). This is separate from mobCount.
A wave may contain only Overlords by setting mobCount to 0 and overlordCount above 0.
Default configuration preserves the original 3 normal waves, 4 Nether-level waves, enemy selection chances, and final Overlord.

