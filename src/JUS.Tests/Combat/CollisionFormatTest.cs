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
    /// Tests for Collision format conversion.
    /// </summary>
    public class CollisionFormatTest
    {
        private string resPath;

        [SetUp]
        public void Setup()
        {
            string programDir = AppDomain.CurrentDomain.BaseDirectory;
            resPath = Path.GetFullPath(programDir + "/../../../Resources/Combat/Collision/");

            Assert.That(Directory.Exists(resPath), Is.True, $"The resources folder does not exist: {resPath}");
        }

        [Test]
        public void CollisionRoundTripTest()
        {
            foreach (string filePath in Directory.GetFiles(resPath, "*.bin", SearchOption.AllDirectories))
            {
                using Node node = NodeFactory.FromFile(filePath);

                // BinaryFormat -> Collision
                BinaryFormat expectedBin = node.GetFormatAs<BinaryFormat>();
                var converter = new Binary2Collision();
                Collision collision = null;

                try
                {
                    collision = converter.Convert(expectedBin);
                }
                catch (Exception ex)
                {
                    Assert.Fail($"Exception BinaryFormat -> Collision with {node.Path}\n{ex}");
                }

                Assert.That(collision, Is.Not.Null);
                Assert.That(collision.Entries.Count, Is.GreaterThan(0), $"No entries in {node.Path}");

                // Collision -> BinaryFormat
                BinaryFormat actualBin = null;
                try
                {
                    actualBin = converter.Convert(collision);
                }
                catch (Exception ex)
                {
                    Assert.Fail($"Exception Collision -> BinaryFormat with {node.Path}\n{ex}");
                }

                // Compare binaries
                expectedBin.Stream.Position = 0;
                actualBin.Stream.Position = 0;
                Assert.That(
                    expectedBin.Stream.Compare(actualBin.Stream),
                    Is.True,
                    $"Collision round-trip failed for: {node.Path}");
            }
        }

        [Test]
        public void CollisionEntrySize()
        {
            Assert.That(CollisionEntry.EntrySize, Is.EqualTo(20));
        }

        [Test]
        public void CollisionEntryCountMatchesFileSize()
        {
            foreach (string filePath in Directory.GetFiles(resPath, "*.bin", SearchOption.AllDirectories))
            {
                var fileInfo = new FileInfo(filePath);
                int expectedCount = (int)(fileInfo.Length / CollisionEntry.EntrySize);

                using Node node = NodeFactory.FromFile(filePath);
                BinaryFormat bin = node.GetFormatAs<BinaryFormat>();
                var converter = new Binary2Collision();
                Collision collision = converter.Convert(bin);

                Assert.That(
                    collision.Entries.Count,
                    Is.EqualTo(expectedCount),
                    $"Entry count mismatch for {filePath}");
            }
        }

        [Test]
        public void CollisionFieldRanges()
        {
            foreach (string filePath in Directory.GetFiles(resPath, "*.bin", SearchOption.AllDirectories))
            {
                using Node node = NodeFactory.FromFile(filePath);
                BinaryFormat bin = node.GetFormatAs<BinaryFormat>();
                var converter = new Binary2Collision();
                Collision collision = converter.Convert(bin);

                foreach (var entry in collision.Entries)
                {
                    // Collision type should be 0-7
                    Assert.That(entry.CollisionType, Is.LessThanOrEqualTo(7),
                        $"Invalid CollisionType in {filePath}");

                    // Hit tier should be 0-3
                    Assert.That(entry.HitTier, Is.LessThanOrEqualTo(3),
                        $"Invalid HitTier in {filePath}");

                    // Reserved fields should be 0
                    Assert.That(entry.Reserved0, Is.EqualTo(0),
                        $"Reserved0 not zero in {filePath}");
                    Assert.That(entry.Reserved1, Is.EqualTo(0),
                        $"Reserved1 not zero in {filePath}");
                }
            }
        }
    }
}
