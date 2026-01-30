// Copyright (c) 2024 JUSToolkit contributors
// Licensed under the MIT license.

using System.Collections.Generic;
using Yarhl.FileFormat;

namespace JUSToolkit.Combat.Formats
{
    /// <summary>
    /// Format for battle character stats file (chr_b.bin).
    /// </summary>
    public class BattleCharacter : IFormat
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="BattleCharacter"/> class.
        /// </summary>
        public BattleCharacter()
        {
            Entries = new List<BattleCharacterEntry>();
        }

        /// <summary>
        /// Gets or sets the list of battle character entries.
        /// </summary>
        public List<BattleCharacterEntry> Entries { get; set; }

        /// <summary>
        /// Gets the number of entries.
        /// </summary>
        public int Count => Entries.Count;
    }
}
