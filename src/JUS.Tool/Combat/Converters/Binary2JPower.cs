// Copyright (c) 2024 JUSToolkit contributors
// Licensed under the MIT license.

using System;
using JUSToolkit.Combat.Formats;
using Yarhl.FileFormat;
using Yarhl.IO;

namespace JUSToolkit.Combat.Converters
{
    /// <summary>
    /// Converts between JPower format and BinaryFormat.
    /// </summary>
    public class Binary2JPower :
        IConverter<BinaryFormat, JPower>,
        IConverter<JPower, BinaryFormat>
    {
        /// <summary>
        /// Converts BinaryFormat to JPower format.
        /// </summary>
        /// <param name="source">BinaryFormat to convert.</param>
        /// <returns>JPower format.</returns>
        /// <exception cref="ArgumentNullException">Source is null.</exception>
        public JPower Convert(BinaryFormat source)
        {
            if (source == null)
            {
                throw new ArgumentNullException(nameof(source));
            }

            var jpower = new JPower();
            var reader = new DataReader(source.Stream)
            {
                Endianness = EndiannessMode.LittleEndian,
            };

            int blockCount = (int)(source.Stream.Length / JPowerEntry.BlockSize);

            for (int i = 0; i < blockCount; i++)
            {
                long blockStart = i * JPowerEntry.BlockSize;

                // Read entire raw block for perfect round-trip
                reader.Stream.Position = blockStart;
                byte[] rawBlock = reader.ReadBytes(JPowerEntry.BlockSize);

                // Parse the main record fields
                reader.Stream.Position = blockStart;
                var entry = ReadEntry(reader);
                entry.RawBlockData = rawBlock;

                // Check if this block has a modifier sub-record (marker = 0x02 at offset 0x40)
                if (rawBlock[64] == 0x02 && rawBlock[65] == 0x00)
                {
                    entry.HasModifier = true;
                    reader.Stream.Position = blockStart + JPowerEntry.SubRecordSize + 8;
                    entry.ModifierDamage1 = reader.ReadUInt16();
                    entry.ModifierDamage2 = reader.ReadUInt16();
                    entry.ModifierDamage3 = reader.ReadUInt16();
                    reader.ReadUInt16(); // reserved
                    reader.ReadUInt16(); // reserved
                    entry.ModifierEffect = reader.ReadUInt16();
                }

                jpower.Entries.Add(entry);
            }

            return jpower;
        }

        /// <summary>
        /// Converts JPower format to BinaryFormat.
        /// </summary>
        /// <param name="jpower">JPower to convert.</param>
        /// <returns>BinaryFormat.</returns>
        /// <exception cref="ArgumentNullException">JPower is null.</exception>
        public BinaryFormat Convert(JPower jpower)
        {
            if (jpower == null)
            {
                throw new ArgumentNullException(nameof(jpower));
            }

            var bin = new BinaryFormat();
            var writer = new DataWriter(bin.Stream)
            {
                Endianness = EndiannessMode.LittleEndian,
            };

            foreach (var entry in jpower.Entries)
            {
                // Write entire raw block (304 bytes)
                writer.Write(entry.RawBlockData);
            }

            return bin;
        }

        private static JPowerEntry ReadEntry(DataReader reader)
        {
            var entry = new JPowerEntry
            {
                Id = reader.ReadUInt16(),
            };

            reader.ReadUInt16(); // reserved

            entry.Type1 = reader.ReadUInt16();
            entry.Type2 = reader.ReadUInt16();
            entry.NextId = reader.ReadUInt16();

            reader.ReadUInt16(); // reserved

            entry.Damage1 = reader.ReadUInt16();
            entry.Damage2 = reader.ReadUInt16();
            entry.Damage3 = reader.ReadUInt16();

            reader.ReadUInt16(); // reserved
            reader.ReadUInt16(); // reserved

            entry.Hitstun = reader.ReadUInt16();
            entry.LinkType = reader.ReadUInt16();
            entry.LinkCategory = reader.ReadUInt16();
            entry.LinkFlags = reader.ReadUInt16();

            reader.ReadUInt16(); // reserved

            entry.ExtendedData = reader.ReadBytes(16);

            return entry;
        }
    }
}
