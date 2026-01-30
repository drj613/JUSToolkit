// Copyright (c) 2024 JUSToolkit contributors
// Licensed under the MIT license.

namespace JUSToolkit.Combat.Formats
{
    /// <summary>
    /// Single battle character entry from chr_b.bin.
    /// </summary>
    public class BattleCharacterEntry
    {
        /// <summary>
        /// Entry size in bytes.
        /// </summary>
        public const int EntrySize = 60;

        /// <summary>
        /// Gets or sets the form type.
        /// 0=Normal, 1=Powered, 2=Transformed. I think?
        /// </summary>
        public byte FormType { get; set; }

        /// <summary>
        /// Gets or sets the character power tier (1-3).
        /// </summary>
        public byte Tier { get; set; }

        /// <summary>
        /// Gets or sets the koma/panel size in deck (2-6).
        /// This is NOT the number of cells a panel takes in the deck. Very confused about what this is
        /// Battle characters take anywhere from 4 to 8 cells
        /// Is this a pointer?
        /// </summary>
        public byte KomaSize { get; set; }

        /// <summary>
        /// Gets or sets the character identifier within series.
        /// </summary>
        public byte CharId { get; set; }

        /// <summary>
        /// Gets or sets the battle flags/modifiers (4 bytes).
        /// </summary>
        public uint Flags { get; set; }

        /// <summary>
        /// Gets or sets primary base stat (2-305 range).
        /// </summary>
        public ushort StatA { get; set; }

        /// <summary>
        /// Gets or sets secondary base stat (1-304 range).
        /// </summary>
        public ushort StatB { get; set; }

        /// <summary>
        /// Gets or sets tertiary base stat (3-300 range).
        /// </summary>
        public ushort StatC { get; set; }

        /// <summary>
        /// Gets or sets the character class identifier.
        /// </summary>
        public ushort ClassId { get; set; }

        /// <summary>
        /// Gets or sets combat stat 1 value.
        /// </summary>
        public ushort CombatStat1Value { get; set; }

        /// <summary>
        /// Gets or sets combat stat 1 modifier.
        /// </summary>
        public ushort CombatStat1Mod { get; set; }

        /// <summary>
        /// Gets or sets combat stat 2 value.
        /// </summary>
        public ushort CombatStat2Value { get; set; }

        /// <summary>
        /// Gets or sets combat stat 2 modifier.
        /// </summary>
        public ushort CombatStat2Mod { get; set; }

        /// <summary>
        /// Gets or sets combat stat 3 value.
        /// </summary>
        public ushort CombatStat3Value { get; set; }

        /// <summary>
        /// Gets or sets combat stat 3 modifier.
        /// </summary>
        public ushort CombatStat3Mod { get; set; }

        /// <summary>
        /// Gets or sets combat stat 4 value.
        /// </summary>
        public ushort CombatStat4Value { get; set; }

        /// <summary>
        /// Gets or sets combat stat 4 modifier.
        /// </summary>
        public ushort CombatStat4Mod { get; set; }

        /// <summary>
        /// Gets or sets combat stat 5 value.
        /// </summary>
        public ushort CombatStat5Value { get; set; }

        /// <summary>
        /// Gets or sets combat stat 5 modifier.
        /// </summary>
        public ushort CombatStat5Mod { get; set; }

        /// <summary>
        /// Gets or sets battle parameters (12 bytes).
        /// Unclear what these are, exactly.
        /// They seem to be related to the character's abilities, "defensive weight" and "attack weight"
        /// As well as some that are just completely unknown
        /// </summary>
        public byte[] BattleParams { get; set; }

        /// <summary>
        /// Gets or sets text IDs for name/moves (6 u16 values).
        /// </summary>
        public ushort[] TextIds { get; set; }

        /// <summary>
        /// Initializes a new instance of the <see cref="BattleCharacterEntry"/> class.
        /// </summary>
        public BattleCharacterEntry()
        {
            BattleParams = new byte[12];
            TextIds = new ushort[6];
        }
    }
}
