export default function ErrorMessage({ message }) {
  if (!message) return null
  return (
    <div className="bg-red-900/40 border border-red-700 text-red-300 rounded px-4 py-3 text-sm my-4">
      {message}
    </div>
  )
}
