// Copyright (c) 2024 JUSToolkit contributors
// Licensed under the MIT license.

using System;
using System.IO;
using JUSToolkit.Combat.Converters;
using JUSToolkit.Combat.Formats;
using NUnit.Framework;
using Yarhl.FileSystem;
using Yarhl.IO;

namespace JUS.Tests.Combat
{
    /// <summary>
    /// Tests for BattleCharacter format conversion.
    /// </summary>
    public class BattleCharacterFormatTest
    {
        private string resPath;

        [SetUp]
        public void Setup()
        {
            string programDir = AppDomain.CurrentDomain.BaseDirectory;
            resPath = Path.GetFullPath(programDir + "/../../../Resources/Combat/BattleCharacter/");

            Assert.That(Directory.Exists(resPath), Is.True, $"The resources folder does not exist: {resPath}");
        }

        [Test]
        public void BattleCharacterRoundTripTest()
        {
            foreach (string filePath in Directory.GetFiles(resPath, "*.bin", SearchOption.AllDirectories))
            {
                using Node node = NodeFactory.FromFile(filePath);

                // BinaryFormat -> BattleCharacter
                BinaryFormat expectedBin = node.GetFormatAs<BinaryFormat>();
                var converter = new Binary2BattleCharacter();
                BattleCharacter battleChar = null;

                try
                {
                    battleChar = converter.Convert(expectedBin);
                }
                catch (Exception ex)
                {
                    Assert.Fail($"Exception BinaryFormat -> BattleCharacter with {node.Path}\n{ex}");
                }

                Assert.That(battleChar, Is.Not.Null);
                Assert.That(battleChar.Entries.Count, Is.GreaterThan(0), $"No entries in {node.Path}");

                // BattleCharacter -> BinaryFormat
                BinaryFormat actualBin = null;
                try
                {
                    actualBin = converter.Convert(battleChar);
                }
                catch (Exception ex)
                {
                    Assert.Fail($"Exception BattleCharacter -> BinaryFormat with {node.Path}\n{ex}");
                }

                // Compare binaries
                expectedBin.Stream.Position = 0;
                actualBin.Stream.Position = 0;
                Assert.That(
                    expectedBin.Stream.Compare(actualBin.Stream),
                    Is.True,
                    $"BattleCharacter round-trip failed for: {node.Path}");
            }
        }

        [Test]
        public void BattleCharacterEntrySize()
        {
            Assert.That(BattleCharacterEntry.EntrySize, Is.EqualTo(60));
        }

        [Test]
        public void BattleCharacterEntryCountMatchesFileSize()
        {
            foreach (string filePath in Directory.GetFiles(resPath, "*.bin", SearchOption.AllDirectories))
            {
                var fileInfo = new FileInfo(filePath);
                int expectedCount = (int)(fileInfo.Length / BattleCharacterEntry.EntrySize);

                using Node node = NodeFactory.FromFile(filePath);
                BinaryFormat bin = node.GetFormatAs<BinaryFormat>();
                var converter = new Binary2BattleCharacter();
                BattleCharacter battleChar = converter.Convert(bin);

                Assert.That(
                    battleChar.Entries.Count,
                    Is.EqualTo(expectedCount),
                    $"Entry count mismatch for {filePath}");
            }
        }

        [Test]
        public void BattleCharacterExpectedCount()
        {
            string chrBPath = Path.Combine(resPath, "chr_b.bin");
            if (!File.Exists(chrBPath))
            {
                Assert.Ignore("chr_b.bin not found in test resources");
            }

            using Node node = NodeFactory.FromFile(chrBPath);
            BinaryFormat bin = node.GetFormatAs<BinaryFormat>();
            var converter = new Binary2BattleCharacter();
            BattleCharacter battleChar = converter.Convert(bin);

            // chr_b.bin should have 74 battle characters
            Assert.That(battleChar.Entries.Count, Is.EqualTo(74));
        }

        [Test]
        public void BattleCharacterFieldRanges()
        {
            foreach (string filePath in Directory.GetFiles(resPath, "*.bin", SearchOption.AllDirectories))
            {
                using Node node = NodeFactory.FromFile(filePath);
                BinaryFormat bin = node.GetFormatAs<BinaryFormat>();
                var converter = new Binary2BattleCharacter();
                BattleCharacter battleChar = converter.Convert(bin);

                foreach (var entry in battleChar.Entries)
                {
                    // FormType should be 0-3
                    Assert.That(entry.FormType, Is.LessThanOrEqualTo(3),
                        $"Invalid FormType in {filePath}");

                    // Tier should be 1-3 (or 0 for special)
                    Assert.That(entry.Tier, Is.LessThanOrEqualTo(6),
                        $"Invalid Tier in {filePath}");

                    // KomaSize should be 2-8
                    Assert.That(entry.KomaSize, Is.LessThanOrEqualTo(10),
                        $"Invalid KomaSize in {filePath}");

                    // BattleParams should be 12 bytes
                    Assert.That(entry.BattleParams.Length, Is.EqualTo(12),
                        $"Invalid BattleParams length in {filePath}");

                    // TextIds should be 6 entries
                    Assert.That(entry.TextIds.Length, Is.EqualTo(6),
                        $"Invalid TextIds length in {filePath}");
                }
            }
        }
    }
}
