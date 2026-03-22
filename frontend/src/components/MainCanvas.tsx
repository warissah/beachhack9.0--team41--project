import { ChevronRight, Zap, Circle, ShieldAlert, Trash2, RotateCcw, ListOrdered, Sparkles, GitBranch } from "lucide-react";
import { useAppContext } from "../context/AppContext";
import { getProgress, getNextTinyStart } from "../utils/taskUtils";
import TaskCard from "./TaskCard";
import type { Task } from "../context/AppContext";

export default function MainCanvas() {
  const { projects, activeProject, activeFilter, toggleSubtask, deleteTask, removeSubtask, restoreTask, deletedTasks, planResponse } = useAppContext();

  let breadcrumb = "All Tasks";
  let displayTasks: Task[] = [];
  let projectColor = "#6366F1";

  if (activeProject) {
    const p = projects.find(x => x.id === activeProject);
    if (p) {
      breadcrumb = p.name;
      displayTasks = p.tasks;
      projectColor = p.color;
    }
  } else if (activeFilter === "urgent") {
    breadcrumb = "Urgent";
    projects.forEach(p => {
      p.tasks.filter(t => t.urgent).forEach(t => displayTasks.push({ ...t, _projectColor: p.color }));
    });
  } else if (activeFilter === "recent") {
    breadcrumb = "Recent";
    projects.forEach(p => {
      displayTasks.push(...p.tasks.slice(0, 2).map(t => ({ ...t, _projectColor: p.color })));
    });
  } else if (activeFilter === "trash") {
    breadcrumb = "Recently Deleted";
  } else {
    breadcrumb = "All Tasks";
    projects.forEach(p => {
      displayTasks.push(...p.tasks.map(t => ({ ...t, _projectColor: p.color })));
    });
  }

  const project = projects.find(x => x.id === activeProject);
  const progress = project ? getProgress(project.tasks) : null;
  const nextTiny = project ? getNextTinyStart(project.tasks) : null;
  const showPlanContract =
    planResponse &&
    activeProject === `plan-${planResponse.plan_id}` &&
    activeFilter !== "trash";

  return (
    <div className="flex-1 min-h-screen" style={{ background: "#FAFBFC" }}>
      <div className="max-w-3xl mx-auto px-6 pt-8 pb-32">
        <div className="flex items-center gap-1.5 text-[13px] text-gray-400 mb-1">
          <span>Projects</span>
          <ChevronRight className="w-3 h-3" />
          <span className="text-gray-700 font-medium">{breadcrumb}</span>
        </div>

        <div className="flex items-end justify-between mb-2">
          <h1 className="text-[28px] font-bold text-gray-900 tracking-tight">
            {project ? `${project.emoji} ${project.name}` : breadcrumb}
          </h1>
          {progress !== null && (
            <span className="text-sm text-gray-400 font-medium">{progress}% complete</span>
          )}
        </div>

        {showPlanContract && (
          <div className="space-y-4 mt-4 mb-6">
            <div className="rounded-xl border border-gray-200/80 bg-white px-4 py-3 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-gray-500 flex-shrink-0" />
                <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Summary</p>
              </div>
              <p className="text-sm text-gray-700 leading-relaxed">{planResponse.summary}</p>
            </div>

            <div className="rounded-xl border border-amber-200/80 bg-amber-50/80 px-4 py-3">
              <p className="text-[11px] font-semibold text-amber-700 uppercase tracking-wider mb-1">Tiny first step</p>
              <p className="text-sm font-semibold text-gray-900">{planResponse.tiny_first_step.title}</p>
              <p className="text-sm text-gray-600 mt-1 leading-relaxed">{planResponse.tiny_first_step.description}</p>
              <p className="text-[12px] text-amber-700/90 mt-2 font-medium">
                ~{planResponse.tiny_first_step.estimated_minutes} min
              </p>
            </div>

            <div className="rounded-xl border border-gray-200/80 bg-white px-4 py-3 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <ListOrdered className="w-4 h-4 text-gray-500 flex-shrink-0" />
                <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Steps</p>
              </div>
              <ol className="space-y-3 list-decimal list-inside marker:text-gray-400">
                {planResponse.steps.map(s => (
                  <li key={s.id} className="text-sm text-gray-800">
                    <span className="font-medium">{s.title}</span>
                    {s.description ? (
                      <span className="block text-gray-600 mt-0.5 pl-0 sm:pl-5 leading-relaxed">{s.description}</span>
                    ) : null}
                    <span className="block text-[12px] text-gray-400 mt-0.5">~{s.estimated_minutes} min</span>
                  </li>
                ))}
              </ol>
            </div>

            <div className="rounded-xl border border-indigo-200/70 bg-indigo-50/50 px-4 py-3">
              <div className="flex items-center gap-2 mb-2">
                <GitBranch className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                <p className="text-[11px] font-semibold text-indigo-700 uppercase tracking-wider">Implementation intention</p>
              </div>
              <p className="text-sm text-gray-800">
                <span className="text-gray-500 font-medium">If </span>
                {planResponse.implementation_intention.if_condition}
              </p>
              <p className="text-sm text-gray-800 mt-2">
                <span className="text-gray-500 font-medium">Then </span>
                {planResponse.implementation_intention.then_action}
              </p>
            </div>

            {planResponse.safety_note.trim() !== "" && (
              <div className="flex items-start gap-3 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl">
                <ShieldAlert className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                <p className="text-[12px] text-gray-500 leading-relaxed">{planResponse.safety_note}</p>
              </div>
            )}
          </div>
        )}

        {nextTiny && (
          <div className="mb-6 mt-4 flex items-center gap-3 px-4 py-3 bg-amber-50 border border-amber-200/70 rounded-xl">
            <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
              <Zap className="w-4 h-4 text-amber-600" />
            </div>
            <div className="min-w-0">
              <p className="text-[11px] font-semibold text-amber-600 uppercase tracking-wider">Your 2-Minute Tiny Start</p>
              <p className="text-sm text-gray-800 font-medium truncate">{nextTiny.title}</p>
            </div>
          </div>
        )}

        <div className="space-y-4 mt-4">
          {displayTasks.map(t => (
            <TaskCard
              key={t.id}
              task={t}
              projectId={activeProject ?? ""}
              projectColor={t._projectColor || projectColor}
              onToggleSubtask={toggleSubtask}
              onDeleteTask={deleteTask}
              onRemoveSubtask={removeSubtask}
            />
          ))}
        </div>

        {/* Trash view */}
        {activeFilter === "trash" ? (
          deletedTasks.length === 0 ? (
            <div className="text-center py-20 text-gray-400">
              <Trash2 className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Nothing in the trash.</p>
            </div>
          ) : (
            <div className="space-y-2 mt-4">
              {deletedTasks.map(d => (
                <div key={d.task.id} className="flex items-center gap-3 px-4 py-3 bg-white border border-gray-200 rounded-xl shadow-sm">
                  <span className="text-base">{d.projectEmoji}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-500 line-through truncate">{d.task.title}</p>
                    <p className="text-[11px] text-gray-400 mt-0.5">{d.projectName}</p>
                  </div>
                  <button
                    onClick={() => restoreTask(d.task.id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium text-gray-600 hover:text-gray-900 bg-gray-50 border border-gray-200 rounded-lg hover:border-gray-300 transition-all flex-shrink-0"
                  >
                    <RotateCcw className="w-3 h-3" /> Restore
                  </button>
                </div>
              ))}
            </div>
          )
        ) : (
          <>
            {displayTasks.length === 0 && (
              <div className="text-center py-20 text-gray-400">
                <Circle className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p className="text-sm">No tasks here yet.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
