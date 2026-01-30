// Copyright (c) 2024 JUSToolkit contributors
// Licensed under the MIT license.

using System.Text.Json.Serialization;

namespace JUSToolkit.Combat.Formats
{
    /// <summary>
    /// Single move/power entry from jpower.bin.
    /// </summary>
    public class JPowerEntry
    {
        /// <summary>
        /// Block size in bytes (contains main record + modifier + padding).
        /// </summary>
        public const int BlockSize = 304;

        /// <summary>
        /// Sub-record size in bytes.
        /// </summary>
        public const int SubRecordSize = 64;

        /// <summary>
        /// Gets or sets the record identifier.
        /// </summary>
        public ushort Id { get; set; }

        /// <summary>
        /// Gets or sets the primary type marker.
        /// 0=data-only, 1=attack definition.
        /// </summary>
        public ushort Type1 { get; set; }

        /// <summary>
        /// Gets or sets the attack subtype.
        /// 1=standard, 7=projectile, 8=heavy, 9=special, 10=super.
        /// </summary>
        public ushort Type2 { get; set; }

        /// <summary>
        /// Gets or sets the next/linked record ID.
        /// </summary>
        public ushort NextId { get; set; }

        /// <summary>
        /// Gets or sets primary damage value.
        /// </summary>
        public ushort Damage1 { get; set; }

        /// <summary>
        /// Gets or sets secondary damage value.
        /// </summary>
        public ushort Damage2 { get; set; }

        /// <summary>
        /// Gets or sets tertiary damage value.
        /// </summary>
        public ushort Damage3 { get; set; }

        /// <summary>
        /// Gets or sets hitstun frames.
        /// 5=light attacks, 10=heavy attacks.
        /// </summary>
        public ushort Hitstun { get; set; }

        /// <summary>
        /// Gets or sets the link type (0 or 2).
        /// </summary>
        public ushort LinkType { get; set; }

        /// <summary>
        /// Gets or sets the link category.
        /// 1=chain, 4=ground, 5=light, 7=launcher, 8=super, 9=multi-hit, 10=finisher.
        /// </summary>
        public ushort LinkCategory { get; set; }

        /// <summary>
        /// Gets or sets link flags.
        /// </summary>
        public ushort LinkFlags { get; set; }

        /// <summary>
        /// Gets or sets the extended data (16 bytes).
        /// </summary>
        public byte[] ExtendedData { get; set; }

        /// <summary>
        /// Gets or sets the raw block data (304 bytes) for perfect round-trip.
        /// This includes main record, modifier record, and extra data section.
        /// </summary>
        [JsonIgnore]
        public byte[] RawBlockData { get; set; }

        /// <summary>
        /// Gets or sets a value indicating whether this record has a modifier sub-record.
        /// </summary>
        public bool HasModifier { get; set; }

        /// <summary>
        /// Gets or sets the modifier damage 1 (typically 2x Damage1).
        /// </summary>
        public ushort ModifierDamage1 { get; set; }

        /// <summary>
        /// Gets or sets the modifier damage 2 (typically 2x Damage2).
        /// </summary>
        public ushort ModifierDamage2 { get; set; }

        /// <summary>
        /// Gets or sets the modifier damage 3 (typically 2x Damage3).
        /// </summary>
        public ushort ModifierDamage3 { get; set; }

        /// <summary>
        /// Gets or sets the modifier effect value.
        /// </summary>
        public ushort ModifierEffect { get; set; }

        /// <summary>
        /// Initializes a new instance of the <see cref="JPowerEntry"/> class.
        /// </summary>
        public JPowerEntry()
        {
            ExtendedData = new byte[16];
            RawBlockData = new byte[BlockSize];
        }

        /// <summary>
        /// Gets the total damage (sum of Damage1, Damage2, Damage3).
        /// </summary>
        public int TotalDamage => Damage1 + Damage2 + Damage3;

        /// <summary>
        /// Gets the attack category name based on Type2.
        /// </summary>
        public string CategoryName => Type2 switch
        {
            0 => "Data",
            1 => "Standard",
            2 => "Variation2",
            3 => "Variation3",
            4 => "Variation4",
            5 => "Variation5",
            7 => "Projectile",
            8 => "Heavy",
            9 => "Special",
            10 => "Super",
            _ => $"Unknown({Type2})",
        };

        /// <summary>
        /// Gets a value indicating whether this is an attack record.
        /// </summary>
        public bool IsAttack => Type1 == 1;
    }
}
