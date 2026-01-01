"use client";

import { useMemo, useState } from "react";

type PadColor = "yellow" | "blue" | "green" | "pink";
type PadFont = "sans" | "serif" | "mono";

export default function Home() {
  const [padColor, setPadColor] = useState<PadColor>("yellow");
  const [padFont, setPadFont] = useState<PadFont>("sans");
  const [taskText, setTaskText] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [savedTasks, setSavedTasks] = useState<
    Array<{
      title: string;
      duration_minutes: number;
      confidence: number;
      parse_method: string;
    }>
  >([]);

  const padTheme = useMemo(() => {
    switch (padColor) {
      case "blue":
        return {
          border: "border-sky-200/80",
          bg: "bg-sky-100",
          headerBg: "bg-sky-200/60",
          headerBorder: "border-sky-200/80",
          headerText: "text-sky-950",
          line: "rgba(2,132,199,0.18)",
          bodyText: "text-sky-950/80",
        } as const;
      case "green":
        return {
          border: "border-emerald-200/80",
          bg: "bg-emerald-100",
          headerBg: "bg-emerald-200/60",
          headerBorder: "border-emerald-200/80",
          headerText: "text-emerald-950",
          line: "rgba(5,150,105,0.18)",
          bodyText: "text-emerald-950/80",
        } as const;
      case "pink":
        return {
          border: "border-pink-200/80",
          bg: "bg-pink-100",
          headerBg: "bg-pink-200/60",
          headerBorder: "border-pink-200/80",
          headerText: "text-pink-950",
          line: "rgba(219,39,119,0.18)",
          bodyText: "text-pink-950/80",
        } as const;
      case "yellow":
      default:
        return {
          border: "border-yellow-300/80",
          bg: "bg-yellow-200",
          headerBg: "bg-yellow-300/60",
          headerBorder: "border-yellow-300/80",
          headerText: "text-yellow-950",
          line: "rgba(120,53,15,0.15)",
          bodyText: "text-yellow-950/80",
        } as const;
    }
  }, [padColor]);

  const fontClass = useMemo(() => {
    switch (padFont) {
      case "mono":
        return "font-mono";
      case "serif":
        // Tailwind doesn't ship a serif stack class by default in v4 without config,
        // so we use an inline style below when serif is selected.
        return "";
      case "sans":
      default:
        return "font-sans";
    }
  }, [padFont]);

  const handleSaveTasks = async () => {
    if (!taskText.trim()) {
      alert("Please enter some tasks first!");
      return;
    }

    setIsSaving(true);
    try {
      // Get current session to extract user ID
      const sessionRes = await fetch("/api/auth/session");
      const session = await sessionRes.json();

      if (!session?.user?.id) {
        throw new Error("Not authenticated. Please sign in.");
      }

      // Call backend directly with Authorization header
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/tasks/batch`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": session.user.id, // Send user ID in header
          },
          body: JSON.stringify({
            raw_text: taskText,
            source: "notepad",
          }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to save tasks");
      }

      const data = await response.json();
      setSavedTasks(data.tasks);
      alert(`Successfully saved ${data.tasks.length} tasks!`);
    } catch (error) {
      console.error("Error saving tasks:", error);
      alert(error instanceof Error ? error.message : "Failed to save tasks");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <main className="flex min-h-[calc(100vh-2rem)] items-center justify-center px-6 py-6">
      <div className="mx-auto flex w-full max-w-5xl flex-col items-center justify-center gap-10">
        <section className="relative w-full max-w-2xl">
          {/* Notepad base */}
          <div
            className={[
              "relative overflow-hidden rounded-2xl border shadow-[0_18px_50px_-20px_rgba(0,0,0,0.45)]",
              padTheme.border,
              padTheme.bg,
              fontClass,
            ].join(" ")}
            style={
              padFont === "serif"
                ? { fontFamily: 'ui-serif, Georgia, Cambria, "Times New Roman", Times, serif' }
                : undefined
            }
          >
            {/* Top binding */}
            <div
              className={[
                "relative flex h-12 items-center justify-center border-b",
                padTheme.headerBorder,
                padTheme.headerBg,
              ].join(" ")}
            >
              <h2
                className={[
                  "text-lg font-semibold tracking-tight",
                  padTheme.headerText,
                ].join(" ")}
              >
                Todays Tasks
              </h2>

              {/* Dropdown (top-right) */}
              <details className="group absolute right-3 top-1/2 -translate-y-1/2">
                <summary
                  className={[
                    "cursor-pointer list-none rounded-md border px-3 py-1.5 text-xs font-medium transition",
                    "border-black/10 bg-white/50 text-black/80 hover:bg-white/70",
                    "dark:border-white/10 dark:bg-white/10 dark:text-white/80 dark:hover:bg-white/15",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-black/20 dark:focus-visible:ring-white/20",
                  ].join(" ")}
                  aria-label="Customize task pad"
                >
                  Customize
                </summary>

                <div className="absolute right-0 z-10 mt-2 w-56 rounded-xl border border-black/10 bg-white p-3 shadow-lg dark:border-white/10 dark:bg-zinc-950">
                  <div className="space-y-3">
                    <div className="space-y-1">
                      <label
                        htmlFor="pad-color"
                        className="block text-xs font-medium text-black/70 dark:text-white/70"
                      >
                        Color
                      </label>
                      <select
                        id="pad-color"
                        value={padColor}
                        onChange={(e) => setPadColor(e.target.value as PadColor)}
                        className="w-full rounded-md border border-black/10 bg-white px-2 py-1.5 text-sm text-black dark:border-white/10 dark:bg-white/5 dark:text-white"
                      >
                        <option value="yellow">Yellow</option>
                        <option value="blue">Blue</option>
                        <option value="green">Green</option>
                        <option value="pink">Pink</option>
                      </select>
                    </div>

                    <div className="space-y-1">
                      <label
                        htmlFor="pad-font"
                        className="block text-xs font-medium text-black/70 dark:text-white/70"
                      >
                        Font
                      </label>
                      <select
                        id="pad-font"
                        value={padFont}
                        onChange={(e) => setPadFont(e.target.value as PadFont)}
                        className="w-full rounded-md border border-black/10 bg-white px-2 py-1.5 text-sm text-black dark:border-white/10 dark:bg-white/5 dark:text-white"
                      >
                        <option value="sans">Sans</option>
                        <option value="serif">Serif</option>
                        <option value="mono">Mono</option>
                      </select>
                    </div>
                  </div>
                </div>
              </details>
            </div>

            {/* Lined paper - Editable Textarea */}
            <div
              className="relative min-h-[420px]"
              style={{
                backgroundImage: `repeating-linear-gradient(to bottom, rgba(0,0,0,0) 0px, rgba(0,0,0,0) 26px, ${padTheme.line} 27px)`,
              }}
            >
              <textarea
                value={taskText}
                onChange={(e) => setTaskText(e.target.value)}
                placeholder="Type your tasks here, one per line&#10;e.g. Buy groceries 30m&#10;Team meeting 1h&#10;Review code"
                className={[
                  "h-full min-h-[420px] w-full resize-none bg-transparent px-8 py-8",
                  "leading-[27px] focus:outline-none",
                  padTheme.bodyText,
                  fontClass,
                ].join(" ")}
                style={
                  padFont === "serif"
                    ? { fontFamily: 'ui-serif, Georgia, Cambria, "Times New Roman", Times, serif' }
                    : undefined
                }
              />
            </div>
          </div>

          {/* Save Button */}
          <div className="mt-6 flex justify-center">
            <button
              onClick={handleSaveTasks}
              disabled={isSaving}
              className={[
                "rounded-lg px-6 py-2.5 text-sm font-semibold shadow-md transition-all",
                "bg-indigo-600 text-white hover:bg-indigo-700 active:scale-95",
                "disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-indigo-600",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2",
              ].join(" ")}
            >
              {isSaving ? "Saving..." : "Save Tasks"}
            </button>
          </div>

          {/* Display Saved Tasks */}
          {savedTasks.length > 0 && (
            <div className="mt-8">
              <h3 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                Saved Tasks ({savedTasks.length})
              </h3>
              <ul className="space-y-3">
                {savedTasks.map((task, idx) => (
                  <li
                    key={idx}
                    className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-3 shadow-sm dark:border-zinc-700 dark:bg-zinc-800"
                  >
                    <span className="text-sm text-zinc-900 dark:text-zinc-100">
                      {task.title}
                    </span>
                    <span className="inline-flex items-center rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-medium text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200">
                      {task.duration_minutes >= 60
                        ? `${Math.floor(task.duration_minutes / 60)}h${
                            task.duration_minutes % 60 > 0
                              ? ` ${task.duration_minutes % 60}m`
                              : ""
                          }`
                        : `${task.duration_minutes}m`}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Subtle drop-shadow / depth */}
          <div className="pointer-events-none absolute -inset-2 -z-10 rounded-3xl bg-black/5 blur-2xl" />
        </section>
      </div>
    </main>
  );
}
