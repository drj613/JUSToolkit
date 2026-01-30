// Copyright (c) 2024 JUSToolkit contributors
// Licensed under the MIT license.

using System;
using System.IO;
using System.Linq;
using JUSToolkit.Combat.Converters;
using JUSToolkit.Combat.Formats;
using NUnit.Framework;
using Yarhl.FileSystem;
using Yarhl.IO;

namespace JUS.Tests.Combat
{
    /// <summary>
    /// Tests for JPower format conversion.
    /// </summary>
    public class JPowerFormatTest
    {
        private string resPath;

        [SetUp]
        public void Setup()
        {
            string programDir = AppDomain.CurrentDomain.BaseDirectory;
            resPath = Path.GetFullPath(programDir + "/../../../Resources/Combat/JPower/");

            Assert.That(Directory.Exists(resPath), Is.True, $"The resources folder does not exist: {resPath}");
        }

        [Test]
        public void JPowerRoundTripTest()
        {
            foreach (string filePath in Directory.GetFiles(resPath, "*.bin", SearchOption.AllDirectories))
            {
                using Node node = NodeFactory.FromFile(filePath);

                // BinaryFormat -> JPower
                BinaryFormat expectedBin = node.GetFormatAs<BinaryFormat>();
                var converter = new Binary2JPower();
                JPower jpower = null;

                try
                {
                    jpower = converter.Convert(expectedBin);
                }
                catch (Exception ex)
                {
                    Assert.Fail($"Exception BinaryFormat -> JPower with {node.Path}\n{ex}");
                }

                Assert.That(jpower, Is.Not.Null);
                Assert.That(jpower.Entries.Count, Is.GreaterThan(0), $"No entries in {node.Path}");

                // JPower -> BinaryFormat
                BinaryFormat actualBin = null;
                try
                {
                    actualBin = converter.Convert(jpower);
                }
                catch (Exception ex)
                {
                    Assert.Fail($"Exception JPower -> BinaryFormat with {node.Path}\n{ex}");
                }

                // Compare binaries
                expectedBin.Stream.Position = 0;
                actualBin.Stream.Position = 0;
                Assert.That(
                    expectedBin.Stream.Compare(actualBin.Stream),
                    Is.True,
                    $"JPower round-trip failed for: {node.Path}");
            }
        }

        [Test]
        public void JPowerBlockSize()
        {
            Assert.That(JPowerEntry.BlockSize, Is.EqualTo(304));
            Assert.That(JPowerEntry.SubRecordSize, Is.EqualTo(64));
        }

        [Test]
        public void JPowerEntryCountMatchesFileSize()
        {
            foreach (string filePath in Directory.GetFiles(resPath, "*.bin", SearchOption.AllDirectories))
            {
                var fileInfo = new FileInfo(filePath);
                int expectedCount = (int)(fileInfo.Length / JPowerEntry.BlockSize);

                using Node node = NodeFactory.FromFile(filePath);
                BinaryFormat bin = node.GetFormatAs<BinaryFormat>();
                var converter = new Binary2JPower();
                JPower jpower = converter.Convert(bin);

                Assert.That(
                    jpower.Entries.Count,
                    Is.EqualTo(expectedCount),
                    $"Entry count mismatch for {filePath}");
            }
        }

        [Test]
        public void JPowerExpectedCount()
        {
            string jpowerPath = Path.Combine(resPath, "jpower.bin");
            if (!File.Exists(jpowerPath))
            {
                Assert.Ignore("jpower.bin not found in test resources");
            }

            using Node node = NodeFactory.FromFile(jpowerPath);
            BinaryFormat bin = node.GetFormatAs<BinaryFormat>();
            var converter = new Binary2JPower();
            JPower jpower = converter.Convert(bin);

            // jpower.bin should have 311 entries
            Assert.That(jpower.Entries.Count, Is.EqualTo(311));
        }

        [Test]
        public void JPowerCategoryNames()
        {
            string jpowerPath = Path.Combine(resPath, "jpower.bin");
            if (!File.Exists(jpowerPath))
            {
                Assert.Ignore("jpower.bin not found in test resources");
            }

            using Node node = NodeFactory.FromFile(jpowerPath);
            BinaryFormat bin = node.GetFormatAs<BinaryFormat>();
            var converter = new Binary2JPower();
            JPower jpower = converter.Convert(bin);

            // Check that we have different category types
            var categories = jpower.Entries.Select(e => e.CategoryName).Distinct().ToList();
            Assert.That(categories, Does.Contain("Standard"));
            Assert.That(categories.Count, Is.GreaterThan(1));
        }

        [Test]
        public void JPowerModifierScaling()
        {
            string jpowerPath = Path.Combine(resPath, "jpower.bin");
            if (!File.Exists(jpowerPath))
            {
                Assert.Ignore("jpower.bin not found in test resources");
            }

            using Node node = NodeFactory.FromFile(jpowerPath);
            BinaryFormat bin = node.GetFormatAs<BinaryFormat>();
            var converter = new Binary2JPower();
            JPower jpower = converter.Convert(bin);

            // Check that modifier damage exists for some entries
            // Note: Not all entries follow a strict 2x pattern
            var entriesWithModifiers = jpower.Entries
                .Where(e => e.HasModifier && e.ModifierDamage1 > 0)
                .ToList();
            Assert.That(entriesWithModifiers.Count, Is.GreaterThan(0), "No entries with modifiers found");

            // Count how many entries have 2x scaling (most common pattern)
            int twoXCount = entriesWithModifiers
                .Where(e => e.Damage1 > 0)
                .Count(e => Math.Abs((double)e.ModifierDamage1 / e.Damage1 - 2.0) < 0.1);

            Assert.That(twoXCount, Is.GreaterThan(entriesWithModifiers.Count / 4),
                "Expected at least 25% of entries to have 2x modifier scaling");
        }

        [Test]
        public void JPowerTotalDamageCalculation()
        {
            var entry = new JPowerEntry
            {
                Damage1 = 30,
                Damage2 = 20,
                Damage3 = 10,
            };

            Assert.That(entry.TotalDamage, Is.EqualTo(60));
        }

        [Test]
        public void JPowerIsAttackProperty()
        {
            var attackEntry = new JPowerEntry { Type1 = 1 };
            var dataEntry = new JPowerEntry { Type1 = 0 };

            Assert.That(attackEntry.IsAttack, Is.True);
            Assert.That(dataEntry.IsAttack, Is.False);
        }
    }
}
