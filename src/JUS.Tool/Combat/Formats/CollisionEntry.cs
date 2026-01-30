// Copyright (c) 2024 JUSToolkit contributors
// Licensed under the MIT license.

namespace JUSToolkit.Combat.Formats
{
    /// <summary>
    /// Single collision/hitbox entry in a character collision file.
    /// </summary>
    public class CollisionEntry
    {
        /// <summary>
        /// Entry size in bytes.
        /// </summary>
        public const int EntrySize = 20;

        /// <summary>
        /// Gets or sets the collision type (0-7).
        /// 3=standard (35%), 4=strong (22%), 5=special (30%).
        /// </summary>
        public byte CollisionType { get; set; }

        /// <summary>
        /// Gets or sets the sub-type/move index (0-15).
        /// 1=jab, 2=combo, 5=launcher, 7=special.
        /// </summary>
        public byte SubType { get; set; }

        /// <summary>
        /// Gets or sets the extended flags (0-3).
        /// </summary>
        public byte ExtFlags { get; set; }

        /// <summary>
        /// Gets or sets the projectile reference.
        /// Negative values (-18 to -34) reference projectile types, 0=melee.
        /// </summary>
        public sbyte ProjectileId { get; set; }

        /// <summary>
        /// Gets or sets the frame when hitbox activates (0-82, typically 0-40).
        /// </summary>
        public byte FrameStart { get; set; }

        /// <summary>
        /// Gets or sets the duration multiplier.
        /// Common values: 0, 10, 14, 15, 20, 30, 50, 64, 100.
        /// </summary>
        public byte DurationMult { get; set; }

        /// <summary>
        /// Gets or sets reserved byte 0 (always 0).
        /// </summary>
        public byte Reserved0 { get; set; }

        /// <summary>
        /// Gets or sets the hit modifier.
        /// Common values: 0, 2, 6, 10, 15, 18, 20, 25, 30.
        /// </summary>
        public byte HitModifier { get; set; }

        /// <summary>
        /// Gets or sets the X position offset (signed).
        /// </summary>
        public sbyte OffsetX { get; set; }

        /// <summary>
        /// Gets or sets the Y position offset (unsigned).
        /// </summary>
        public byte OffsetY { get; set; }

        /// <summary>
        /// Gets or sets position flags.
        /// 0x00=standard, 0x02=alternate, 0x20=aerial.
        /// </summary>
        public byte PositionFlags { get; set; }

        /// <summary>
        /// Gets or sets reserved byte 1 (always 0).
        /// </summary>
        public byte Reserved1 { get; set; }

        /// <summary>
        /// Gets or sets the hitbox width (signed, -40 to +47).
        /// </summary>
        public sbyte Width { get; set; }

        /// <summary>
        /// Gets or sets the hitbox height (signed, -33 to +40).
        /// </summary>
        public sbyte Height { get; set; }

        /// <summary>
        /// Gets or sets the damage flags.
        /// WARNING: This is NOT raw damage! In-game testing shows collision damageFlags
        /// values (2,5,3,8,10,14) do not match actual damage (10,10,9,10,15,18).
        /// This field likely encodes a modifier type, index, or effect reference.
        /// 0xFF = terminator entry.
        /// </summary>
        public byte DamageFlags { get; set; }

        /// <summary>
        /// Gets or sets the knockback force (0-69, 0xFF = terminator).
        /// </summary>
        public byte Knockback { get; set; }

        /// <summary>
        /// Gets or sets the hit tier/attack strength.
        /// 0=passive, 1=light, 2=medium, 3=heavy.
        /// </summary>
        public byte HitTier { get; set; }

        /// <summary>
        /// Gets or sets additional hit properties (0-6).
        /// </summary>
        public byte HitProperties { get; set; }

        /// <summary>
        /// Gets or sets reserved byte 2 (always 0).
        /// </summary>
        public byte Reserved2 { get; set; }

        /// <summary>
        /// Gets or sets reserved byte 3 (always 0).
        /// </summary>
        public byte Reserved3 { get; set; }

        /// <summary>
        /// Gets a value indicating whether this is a terminator record.
        /// </summary>
        public bool IsTerminator => DamageFlags == 0xFF || Knockback == 0xFF;

        /// <summary>
        /// Gets the low 6 bits of DamageFlags.
        /// WARNING: This is NOT actual damage - see DamageFlags comment.
        /// </summary>
        public int DamageFlagsLow => DamageFlags & 0x3F;

        /// <summary>
        /// Gets a value indicating whether the special damage flag is set.
        /// </summary>
        public bool HasSpecialFlag => (DamageFlags & 0x40) != 0;
    }
}
