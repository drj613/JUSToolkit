// Copyright (c) 2024 JUSToolkit contributors
// Licensed under the MIT license.

using System;
using JUSToolkit.Combat.Formats;
using Yarhl.FileFormat;
using Yarhl.IO;

namespace JUSToolkit.Combat.Converters
{
    /// <summary>
    /// Converts between Collision format and BinaryFormat.
    /// </summary>
    public class Binary2Collision :
        IConverter<BinaryFormat, Collision>,
        IConverter<Collision, BinaryFormat>
    {
        /// <summary>
        /// Converts BinaryFormat to Collision format.
        /// </summary>
        /// <param name="source">BinaryFormat to convert.</param>
        /// <returns>Collision format.</returns>
        /// <exception cref="ArgumentNullException">Source is null.</exception>
        public Collision Convert(BinaryFormat source)
        {
            if (source == null)
            {
                throw new ArgumentNullException(nameof(source));
            }

            var collision = new Collision();
            var reader = new DataReader(source.Stream)
            {
                Endianness = EndiannessMode.LittleEndian,
            };

            int count = (int)(source.Stream.Length / CollisionEntry.EntrySize);

            for (int i = 0; i < count; i++)
            {
                collision.Entries.Add(ReadEntry(reader));
            }

            return collision;
        }

        /// <summary>
        /// Converts Collision format to BinaryFormat.
        /// </summary>
        /// <param name="collision">Collision to convert.</param>
        /// <returns>BinaryFormat.</returns>
        /// <exception cref="ArgumentNullException">Collision is null.</exception>
        public BinaryFormat Convert(Collision collision)
        {
            if (collision == null)
            {
                throw new ArgumentNullException(nameof(collision));
            }

            var bin = new BinaryFormat();
            var writer = new DataWriter(bin.Stream)
            {
                Endianness = EndiannessMode.LittleEndian,
            };

            foreach (var entry in collision.Entries)
            {
                WriteEntry(writer, entry);
            }

            return bin;
        }

        private static CollisionEntry ReadEntry(DataReader reader)
        {
            var entry = new CollisionEntry
            {
                CollisionType = reader.ReadByte(),
                SubType = reader.ReadByte(),
                ExtFlags = reader.ReadByte(),
                ProjectileId = reader.ReadSByte(),
                FrameStart = reader.ReadByte(),
                DurationMult = reader.ReadByte(),
                Reserved0 = reader.ReadByte(),
                HitModifier = reader.ReadByte(),
                OffsetX = reader.ReadSByte(),
                OffsetY = reader.ReadByte(),
                PositionFlags = reader.ReadByte(),
                Reserved1 = reader.ReadByte(),
                Width = reader.ReadSByte(),
                Height = reader.ReadSByte(),
                DamageFlags = reader.ReadByte(),
                Knockback = reader.ReadByte(),
                HitTier = reader.ReadByte(),
                HitProperties = reader.ReadByte(),
                Reserved2 = reader.ReadByte(),
                Reserved3 = reader.ReadByte(),
            };

            return entry;
        }

        private static void WriteEntry(DataWriter writer, CollisionEntry entry)
        {
            writer.Write(entry.CollisionType);
            writer.Write(entry.SubType);
            writer.Write(entry.ExtFlags);
            writer.Write(entry.ProjectileId);
            writer.Write(entry.FrameStart);
            writer.Write(entry.DurationMult);
            writer.Write(entry.Reserved0);
            writer.Write(entry.HitModifier);
            writer.Write(entry.OffsetX);
            writer.Write(entry.OffsetY);
            writer.Write(entry.PositionFlags);
            writer.Write(entry.Reserved1);
            writer.Write(entry.Width);
            writer.Write(entry.Height);
            writer.Write(entry.DamageFlags);
            writer.Write(entry.Knockback);
            writer.Write(entry.HitTier);
            writer.Write(entry.HitProperties);
            writer.Write(entry.Reserved2);
            writer.Write(entry.Reserved3);
        }
    }
}
