import { useStore } from "../stores/useStore";

const borderColors = {
  error: "border-l-red-500",
  success: "border-l-green-500",
  info: "border-l-blue-500",
};

export default function ToastContainer() {
  const notifications = useStore((s) => s.notifications);
  const removeNotification = useStore((s) => s.removeNotification);

  if (notifications.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {notifications.map((n) => (
        <div
          key={n.id}
          className={`bg-neutral-50 dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 border-l-4 ${borderColors[n.type]} rounded px-4 py-3 shadow-lg flex items-start gap-3`}
        >
          <p className="text-sm text-neutral-800 dark:text-neutral-200 flex-1">{n.message}</p>
          <button
            onClick={() => removeNotification(n.id)}
            className="text-neutral-400 dark:text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 text-lg leading-none"
          >
            &times;
          </button>
        </div>
      ))}
    </div>
  );
}
