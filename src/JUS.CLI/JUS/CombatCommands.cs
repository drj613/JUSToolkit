// Copyright (c) 2024 JUSToolkit contributors
// Licensed under the MIT license.

using System;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using JUSToolkit.Combat.Converters;
using JUSToolkit.Combat.Formats;
using Yarhl.FileSystem;
using Yarhl.IO;

namespace JUSToolkit.CLI.JUS
{
    /// <summary>
    /// Commands for exporting combat data files.
    /// </summary>
    public static class CombatCommands
    {
        private static readonly JsonSerializerOptions JsonOptions = new()
        {
            WriteIndented = true,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        };

        /// <summary>
        /// Export a collision .bin file to JSON.
        /// </summary>
        /// <param name="bin">Path to the collision .bin file.</param>
        /// <param name="output">Output directory.</param>
        public static void ExportCollision(string bin, string output)
        {
            Console.WriteLine($"Exporting collision: {bin}");

            using Node binNode = NodeFactory.FromFile(bin, FileOpenMode.Read)
                ?? throw new FormatException("Invalid bin file");

            var binaryFormat = binNode.GetFormatAs<BinaryFormat>();
            var converter = new Binary2Collision();
            Collision collision = converter.Convert(binaryFormat);

            collision.CharacterId = Path.GetFileNameWithoutExtension(bin);

            string outputFile = Path.Combine(output, $"{collision.CharacterId}_collision.json");
            Directory.CreateDirectory(output);

            string json = JsonSerializer.Serialize(collision, JsonOptions);
            File.WriteAllText(outputFile, json);

            Console.WriteLine($"Exported {collision.Count} collision entries to {outputFile}");
            Console.WriteLine("Done!");
        }

        /// <summary>
        /// Export chr_b.bin to JSON.
        /// </summary>
        /// <param name="bin">Path to chr_b.bin.</param>
        /// <param name="output">Output directory.</param>
        public static void ExportBattleCharacter(string bin, string output)
        {
            Console.WriteLine($"Exporting battle characters: {bin}");

            using Node binNode = NodeFactory.FromFile(bin, FileOpenMode.Read)
                ?? throw new FormatException("Invalid bin file");

            var binaryFormat = binNode.GetFormatAs<BinaryFormat>();
            var converter = new Binary2BattleCharacter();
            BattleCharacter battleChar = converter.Convert(binaryFormat);

            string outputFile = Path.Combine(output, "chr_b.json");
            Directory.CreateDirectory(output);

            string json = JsonSerializer.Serialize(battleChar, JsonOptions);
            File.WriteAllText(outputFile, json);

            Console.WriteLine($"Exported {battleChar.Count} battle character entries to {outputFile}");
            Console.WriteLine("Done!");
        }

        /// <summary>
        /// Export jpower.bin to JSON.
        /// </summary>
        /// <param name="bin">Path to jpower.bin.</param>
        /// <param name="output">Output directory.</param>
        public static void ExportJPower(string bin, string output)
        {
            Console.WriteLine($"Exporting jpower: {bin}");

            using Node binNode = NodeFactory.FromFile(bin, FileOpenMode.Read)
                ?? throw new FormatException("Invalid bin file");

            var binaryFormat = binNode.GetFormatAs<BinaryFormat>();
            var converter = new Binary2JPower();
            JPower jpower = converter.Convert(binaryFormat);

            string outputFile = Path.Combine(output, "jpower.json");
            Directory.CreateDirectory(output);

            string json = JsonSerializer.Serialize(jpower, JsonOptions);
            File.WriteAllText(outputFile, json);

            Console.WriteLine($"Exported {jpower.Count} jpower entries to {outputFile}");
            Console.WriteLine("Done!");
        }

        /// <summary>
        /// Batch export all collision files from ChrBin.aar/chr/col/ directory.
        /// </summary>
        /// <param name="directory">Directory containing collision .bin files.</param>
        /// <param name="output">Output directory.</param>
        public static void ExportAllCollisions(string directory, string output)
        {
            Console.WriteLine($"Batch exporting collisions from: {directory}");

            Directory.CreateDirectory(output);
            int count = 0;

            foreach (string binPath in Directory.GetFiles(directory, "*.bin"))
            {
                using Node binNode = NodeFactory.FromFile(binPath, FileOpenMode.Read)
                    ?? throw new FormatException($"Invalid bin file: {binPath}");

                var binaryFormat = binNode.GetFormatAs<BinaryFormat>();
                var converter = new Binary2Collision();
                Collision collision = converter.Convert(binaryFormat);

                collision.CharacterId = Path.GetFileNameWithoutExtension(binPath);

                string outputFile = Path.Combine(output, $"{collision.CharacterId}_collision.json");
                string json = JsonSerializer.Serialize(collision, JsonOptions);
                File.WriteAllText(outputFile, json);

                count++;
            }

            Console.WriteLine($"Exported {count} collision files to {output}");
            Console.WriteLine("Done!");
        }

        /// <summary>
        /// Export all combat data (collision, character, jpower) in one command.
        /// </summary>
        /// <param name="binDir">Directory containing bin files (chr_b.bin, jpower.bin).</param>
        /// <param name="colDir">Directory containing collision .bin files.</param>
        /// <param name="output">Output directory.</param>
        public static void ExportAll(string binDir, string colDir, string output)
        {
            Console.WriteLine("Exporting all combat data...");
            Directory.CreateDirectory(output);

            // Export chr_b.bin
            string chrBPath = Path.Combine(binDir, "chr_b.bin");
            if (File.Exists(chrBPath))
            {
                ExportBattleCharacter(chrBPath, output);
            }
            else
            {
                Console.WriteLine($"Warning: {chrBPath} not found, skipping.");
            }

            // Export jpower.bin
            string jpowerPath = Path.Combine(binDir, "jpower.bin");
            if (File.Exists(jpowerPath))
            {
                ExportJPower(jpowerPath, output);
            }
            else
            {
                Console.WriteLine($"Warning: {jpowerPath} not found, skipping.");
            }

            // Export collision files
            if (Directory.Exists(colDir))
            {
                string colOutput = Path.Combine(output, "collision");
                ExportAllCollisions(colDir, colOutput);
            }
            else
            {
                Console.WriteLine($"Warning: {colDir} not found, skipping collision export.");
            }

            Console.WriteLine("All combat data exported!");
        }
    }
}
