using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

internal static class AIDailyLauncher
{
    [STAThread]
    private static int Main(string[] args)
    {
        string baseDir = AppDomain.CurrentDomain.BaseDirectory;
        string appPath = Path.Combine(baseDir, "AI Daily", "AI Daily.exe");
        if (!File.Exists(appPath))
        {
            MessageBox.Show(
                "Packaged runtime not found:\n" + appPath,
                "AI Daily",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error);
            return 2;
        }

        var startInfo = new ProcessStartInfo
        {
            FileName = appPath,
            WorkingDirectory = Path.GetDirectoryName(appPath),
            UseShellExecute = false,
            RedirectStandardError = true,
            CreateNoWindow = false,
        };

        startInfo.Arguments = string.Join(" ", Array.ConvertAll(args, QuoteArgument));

        using (Process child = Process.Start(startInfo))
        {
            string stderr = child.StandardError.ReadToEnd();
            child.WaitForExit();
            if (!string.IsNullOrWhiteSpace(stderr))
            {
                Console.Error.Write(stderr);
            }
            return child.ExitCode;
        }
    }

    private static string QuoteArgument(string value)
    {
        if (string.IsNullOrEmpty(value))
        {
            return "\"\"";
        }
        if (value.IndexOfAny(new[] { ' ', '\t', '"' }) < 0)
        {
            return value;
        }

        var quoted = new System.Text.StringBuilder();
        quoted.Append('"');
        int pendingBackslashes = 0;
        foreach (char character in value)
        {
            if (character == '\\')
            {
                pendingBackslashes += 1;
                continue;
            }
            if (character == '"')
            {
                quoted.Append('\\', pendingBackslashes * 2 + 1);
                quoted.Append('"');
                pendingBackslashes = 0;
                continue;
            }
            quoted.Append('\\', pendingBackslashes);
            pendingBackslashes = 0;
            quoted.Append(character);
        }
        quoted.Append('\\', pendingBackslashes * 2);
        quoted.Append('"');
        return quoted.ToString();
    }
}
