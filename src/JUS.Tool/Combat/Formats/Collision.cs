// Copyright (c) 2024 JUSToolkit contributors
// Licensed under the MIT license.

using System.Collections.Generic;
using Yarhl.FileFormat;

namespace JUSToolkit.Combat.Formats
{
    /// <summary>
    /// Format for character collision/hitbox files (col/*.bin).
    /// </summary>
    public class Collision : IFormat
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="Collision"/> class.
        /// </summary>
        public Collision()
        {
            Entries = new List<CollisionEntry>();
        }

        /// <summary>
        /// Gets or sets the character identifier (from filename).
        /// </summary>
        public string CharacterId { get; set; }

        /// <summary>
        /// Gets or sets the list of collision entries.
        /// </summary>
        public List<CollisionEntry> Entries { get; set; }

        /// <summary>
        /// Gets the number of entries.
        /// </summary>
        public int Count => Entries.Count;
    }
}
