// Copyright (c) 2024 JUSToolkit contributors
// Licensed under the MIT license.

using System;
using JUSToolkit.Combat.Formats;
using Yarhl.FileFormat;
using Yarhl.IO;

namespace JUSToolkit.Combat.Converters
{
    /// <summary>
    /// Converts between BattleCharacter format and BinaryFormat.
    /// </summary>
    public class Binary2BattleCharacter :
        IConverter<BinaryFormat, BattleCharacter>,
        IConverter<BattleCharacter, BinaryFormat>
    {
        /// <summary>
        /// Converts BinaryFormat to BattleCharacter format.
        /// </summary>
        /// <param name="source">BinaryFormat to convert.</param>
        /// <returns>BattleCharacter format.</returns>
        /// <exception cref="ArgumentNullException">Source is null.</exception>
        public BattleCharacter Convert(BinaryFormat source)
        {
            if (source == null)
            {
                throw new ArgumentNullException(nameof(source));
            }

            var battleChar = new BattleCharacter();
            var reader = new DataReader(source.Stream)
            {
                Endianness = EndiannessMode.LittleEndian,
            };

            int count = (int)(source.Stream.Length / BattleCharacterEntry.EntrySize);

            for (int i = 0; i < count; i++)
            {
                battleChar.Entries.Add(ReadEntry(reader));
            }

            return battleChar;
        }

        /// <summary>
        /// Converts BattleCharacter format to BinaryFormat.
        /// </summary>
        /// <param name="battleChar">BattleCharacter to convert.</param>
        /// <returns>BinaryFormat.</returns>
        /// <exception cref="ArgumentNullException">BattleCharacter is null.</exception>
        public BinaryFormat Convert(BattleCharacter battleChar)
        {
            if (battleChar == null)
            {
                throw new ArgumentNullException(nameof(battleChar));
            }

            var bin = new BinaryFormat();
            var writer = new DataWriter(bin.Stream)
            {
                Endianness = EndiannessMode.LittleEndian,
            };

            foreach (var entry in battleChar.Entries)
            {
                WriteEntry(writer, entry);
            }

            return bin;
        }

        private static BattleCharacterEntry ReadEntry(DataReader reader)
        {
            var entry = new BattleCharacterEntry
            {
                FormType = reader.ReadByte(),
                Tier = reader.ReadByte(),
                KomaSize = reader.ReadByte(),
                CharId = reader.ReadByte(),
                Flags = reader.ReadUInt32(),
                StatA = reader.ReadUInt16(),
                StatB = reader.ReadUInt16(),
                StatC = reader.ReadUInt16(),
                ClassId = reader.ReadUInt16(),
                CombatStat1Value = reader.ReadUInt16(),
                CombatStat1Mod = reader.ReadUInt16(),
                CombatStat2Value = reader.ReadUInt16(),
                CombatStat2Mod = reader.ReadUInt16(),
                CombatStat3Value = reader.ReadUInt16(),
                CombatStat3Mod = reader.ReadUInt16(),
                CombatStat4Value = reader.ReadUInt16(),
                CombatStat4Mod = reader.ReadUInt16(),
                CombatStat5Value = reader.ReadUInt16(),
                CombatStat5Mod = reader.ReadUInt16(),
            };

            entry.BattleParams = reader.ReadBytes(12);
            for (int i = 0; i < 6; i++)
            {
                entry.TextIds[i] = reader.ReadUInt16();
            }

            return entry;
        }

        private static void WriteEntry(DataWriter writer, BattleCharacterEntry entry)
        {
            writer.Write(entry.FormType);
            writer.Write(entry.Tier);
            writer.Write(entry.KomaSize);
            writer.Write(entry.CharId);
            writer.Write(entry.Flags);
            writer.Write(entry.StatA);
            writer.Write(entry.StatB);
            writer.Write(entry.StatC);
            writer.Write(entry.ClassId);
            writer.Write(entry.CombatStat1Value);
            writer.Write(entry.CombatStat1Mod);
            writer.Write(entry.CombatStat2Value);
            writer.Write(entry.CombatStat2Mod);
            writer.Write(entry.CombatStat3Value);
            writer.Write(entry.CombatStat3Mod);
            writer.Write(entry.CombatStat4Value);
            writer.Write(entry.CombatStat4Mod);
            writer.Write(entry.CombatStat5Value);
            writer.Write(entry.CombatStat5Mod);
            writer.Write(entry.BattleParams);
            foreach (var textId in entry.TextIds)
            {
                writer.Write(textId);
            }
        }
    }
}
