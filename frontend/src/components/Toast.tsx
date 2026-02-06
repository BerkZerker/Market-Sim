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
          className={`bg-gray-900 border border-gray-700 border-l-4 ${borderColors[n.type]} rounded px-4 py-3 shadow-lg flex items-start gap-3`}
        >
          <p className="text-sm text-gray-200 flex-1">{n.message}</p>
          <button
            onClick={() => removeNotification(n.id)}
            className="text-gray-500 hover:text-gray-300 text-lg leading-none"
          >
            &times;
          </button>
        </div>
      ))}
    </div>
  );
}
