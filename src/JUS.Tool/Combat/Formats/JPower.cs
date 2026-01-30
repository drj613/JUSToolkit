// Copyright (c) 2024 JUSToolkit contributors
// Licensed under the MIT license.

using System.Collections.Generic;
using Yarhl.FileFormat;

namespace JUSToolkit.Combat.Formats
{
    /// <summary>
    /// Format for move/power parameter file (jpower.bin).
    /// </summary>
    public class JPower : IFormat
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="JPower"/> class.
        /// </summary>
        public JPower()
        {
            Entries = new List<JPowerEntry>();
        }

        /// <summary>
        /// Gets or sets the list of power/move entries.
        /// </summary>
        public List<JPowerEntry> Entries { get; set; }

        /// <summary>
        /// Gets the number of entries.
        /// </summary>
        public int Count => Entries.Count;
    }
}
